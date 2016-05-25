"""
This file defines the 'netconifyCmdo' class.
Used by the 'netconify' shell utility.
"""
import os
import json
import warnings
import traceback
from lxml import etree

from jnpr.junos.transport.tty_telnet import Telnet
from jnpr.junos.transport.tty_ssh import SecureShell
from jnpr.junos.transport.tty_serial import Serial
from jnpr.junos.rpcmeta import _RpcMetaExec
from jnpr.junos import exception as EzErrors


QFX_MODEL_LIST = ['QFX3500', 'QFX3600', 'VIRTUAL CHASSIS']
QFX_MODE_NODE = 'NODE'
QFX_MODE_SWITCH = 'SWITCH'


class Console(object):

    # ------------------------------------------------------------------------
    # property: hostname
    # ------------------------------------------------------------------------

    @property
    def hostname(self):
        """
        :returns: the host-name of the Junos device.
        """
        return self._hostname

    # ------------------------------------------------------------------------
    # property: user
    # ------------------------------------------------------------------------

    @property
    def user(self):
        """
        :returns: the login user (str) accessing the Junos device
        """
        return self._auth_user

    # ------------------------------------------------------------------------
    # property: password
    # ------------------------------------------------------------------------

    @property
    def password(self):
        """
        :returns: ``None`` - do not provide the password
        """
        return None  # read-only

    @password.setter
    def password(self, value):
        """
        Change the authentication password value.  This is handy in case
        the calling program needs to attempt different passwords.
        """
        self._auth_password = value

    # ------------------------------------------------------------------------
    # property: port
    # ------------------------------------------------------------------------

    @property
    def port(self):
        """
        :returns: the port (str) to connect to the Junos device
        """
        return self._port

    # ------------------------------------------------------------------------
    # property: facts
    # ------------------------------------------------------------------------

    @property
    def facts(self):
        """
        :returns: Device fact dictionary
        """
        return self._facts

    @facts.setter
    def facts(self, value):
        """ read-only property """
        raise RuntimeError("facts is read-only!")

    def __init__(self, *args, **kvargs):
        """
        NoobDevice object constructor.

        :param str host:
            **REQUIRED** host-name or ipaddress of target device

        :param str user:
            *OPTIONAL* login user-name, uses $USER if not provided

        :param str passwd:
            *OPTIONAL* if not provided, assumed ssh-keys are enforced

        :param int port:
            *OPTIONAL*  port

        :param bool gather_facts:
            *OPTIONAL* default is ``True``.  If ``False`` then the
            facts are not gathered on call to :meth:`open`

        """

        # ----------------------------------------
        # setup instance connection/open variables
        # ----------------------------------------

        self._tty = None
        self._facts = {}
        self.connected = False
        self._skip_logout = False
        self.on_notify = kvargs.get('notify', None)
        self.results = dict(changed=False, failed=False, errmsg=None)

        self._hostname = kvargs.get('host')
        if self._hostname is None:
            raise ValueError("You must provide the 'host' value")

        self._auth_user = kvargs.get('user', 'root')
        self._auth_password = kvargs.get('password') or kvargs.get('passwd')
        self._port = kvargs.get('port', '/dev/ttyUSB0')
        self._baud = kvargs.get('baud', '9600')
        self._mode = kvargs.get('mode', 'telnet')
        self._timeout = kvargs.get('timeout', '0.5')
        self._attempts = kvargs.get('attempts', 10)
        self.gather_facts = kvargs.get('gather_facts', False)
        self.rpc = _RpcMetaExec(self)

    def open(self):
        """
        open the connection to the device
        """

        # ---------------------------------------------------------------
        # validate device hostname or IP address
        # ---------------------------------------------------------------

        if self._hostname is None:
             self.results['failed'] = True
             self.results['errmsg'] = 'ERROR: Device hostname/IP not specified !!!'
             return self.results

        # --------------------
        # login to the CONSOLE
        # --------------------

        try:
            self._tty_login()
        except Exception as err:
            self._hook_exception('login', err)
            traceback.print_exc()
        self.connected = True


        if self.gather_facts is True:
            self._gather_facts()

        return self


    def close(self, skip_logout = True):
        """
        Closes the connection to the device.
        """
        if skip_logout is False and self.connected is True:
            try:
                self._tty_logout()
            except Exception as err:
                self._hook_exception('logout', err)
            self.connected = False
        elif self.connected is True:
            try:
                self._tty._tty_close()
            except Exception as err:
                self._hook_exception('close', err)
                traceback.print_exc()
            self.connected = False

    def cli(self, command, format='text', warning=True):
        """
        Executes the CLI command and returns the CLI text output by default.

        :param str command:
          The CLI command to execute, e.g. "show version"

        :param str format:
          The return format, by default is text.  You can optionally select
          "xml" to return the XML structure.

        .. note::
            You can also use this method to obtain the XML RPC command for a
            given CLI command by using the pipe filter ``| display xml rpc``. When
            you do this, the return value is the XML RPC command. For example if
            you provide as the command ``show version | display xml rpc``, you will
            get back the XML Element ``<get-software-information>``.

        .. warning::
            This function is provided for **DEBUG** purposes only!
            **DO NOT** use this method for general automation purposes as
            that puts you in the realm of "screen-scraping the CLI".  The purpose of
            the PyEZ framework is to migrate away from that tooling pattern.
            Interaction with the device should be done via the RPC function.

        .. warning::
            You cannot use "pipe" filters with **command** such as ``| match``
            or ``| count``, etc.  The only value use of the "pipe" is for the
            ``| display xml rpc`` as noted above.
        """
        if 'display xml rpc' not in command and warning is True:
            warnings.simplefilter("always")
            warnings.warn("CLI command is for debug use only!", RuntimeWarning)
            warnings.resetwarnings()

        try:
            rsp = self.rpc.cli(command, format)
            if isinstance(rsp, dict) and format.lower() == 'json':
                return rsp
            # rsp returned True means <rpc-reply> is empty, hence return
            # empty str as would be the case on cli
            # ex:
            # <rpc-reply message-id="urn:uuid:281f624f-022b-11e6-bfa8">
            # </rpc-reply>
            if rsp is True:
                return ''
            if rsp.tag in ['output', 'rpc-reply']:
                return rsp.text
            if rsp.tag == 'configuration-information':
                return rsp.findtext('configuration-output')
            if rsp.tag == 'rpc':
                return rsp[0]
            return rsp
        except EzErrors.RpcError as ex:
            if ex.message is not '':
                return "%s: %s" % (ex.message, command)
            else:
                return "invalid command: " + command
        except Exception as ex:
            return "invalid command: " + command

    # execute rpc calls
    def execute(self, rpc_cmd, **kwargs):
        return self._tty.nc.rpc(etree.tounicode(rpc_cmd))


    # -------------------------------------------------------------------------
    # Handlers
    # -------------------------------------------------------------------------

    def _hook_exception(self, event, err):
        self._notify("ERROR", "{0}:{1}\n".format(event, str(err)))
        raise

    def _tty_notifier(self, tty, event, message):
        self._notify("{0}".format(event), message)

    # replace it with log module
    #
    #
    def _notify(self, event, message):
        if self.on_notify is not None:
            self.on_notify(self, event, message)
        elif self.on_notify is not False:
            print("{0}:{1}".format(event, message))

    # -------------------------------------------------------------------------
    # LOGIN/LOGOUT
    # -------------------------------------------------------------------------

    def _tty_login(self):
        ### hack for now
        ### problem in importing at top, because of circular import issue
        tty_args = {}
        tty_args['user'] = self._auth_user
        tty_args['passwd'] = self._auth_password
        tty_args['timeout'] = float(self._timeout)
        tty_args['attempts'] = int(self._attempts)

        if self._mode.upper() == 'TELNET':
            tty_args['host'] = self._hostname
            tty_args['port'] = self._port
            self.console = ('telnet', self._hostname, self.port)
            self._tty = Telnet(**tty_args)
        elif self._mode.upper() == 'SSH':
            tty_args['host'] = self._hostname
            tty_args['port'] = self._port
            tty_args['s_user'] = self._auth_user
            tty_args['s_passwd'] = self._auth_password
            self.console = ('ssh', self._hostname, self._port, self._auth_user, self._auth_password)
            self._tty = SecureShell(**tty_args)
        else:
            tty_args['port'] = self._port
            tty_args['baud'] = self._baud
            self.console = ('serial', self._port)
            self._tty = Serial(**tty_args)

        notify = self.on_notify or self._tty_notifier
        self._tty.login(notify=notify)

    def _tty_logout(self):
        self._tty.logout()


    def _srx_cluster(self, cluster_id, node):
        """ Enable cluster mode on SRX device"""
        srx_args = {}
        srx_args['cluster_id'] = cluster_id
        srx_args['node'] = node
        self._notify('srx_cluster', 'set device to cluster mode, rebooting')
        self._notify('srx_cluster', 'Cluster ID: {0}'.format(cluster_id))
        self._notify('srx_cluster', 'Node: {0}'.format(node))
        self._tty.nc.enablecluster(cluster_id, node)
        self._skip_logout = True
        self.results['changed'] = True

    def _srx_cluster_disable(self):
        """ Disable cluster mode on SRX device"""
        self._notify(
            'srx_cluster',
            'disable cluster mode on srx device, rebooting')
        self._tty.nc.disablecluster()
        self._skip_logout = True
        self.results['changed'] = True

    def _zeroize(self):
        """ perform device ZEROIZE actions """
        self._notify('zeroize', 'ZEROIZE device, rebooting')
        self._tty.nc.zeroize()
        self._skip_logout = True
        self.results['changed'] = True

    def _shutdown(self, mode):
        """ shutdown or reboot """
        self._skip_logout = True
        self._notify('shutdown', 'shutdown {0}'.format(mode))
        nc = self._tty.nc
        shutdown = nc.poweroff if mode == 'poweroff' else nc.reboot
        shutdown()
        self._skip_logout = True
        self.results['changed'] = True

    def _save_facts_json(self, savedir= os.getcwd(), no_save= True):
        if no_save is True:
            self._notify('facts', '{0}'.format(self._facts))
            return
        fname = self._save_name + '-facts.json'
        path = os.path.join(savedir, fname)
        self._notify('facts', 'saving: {0}'.format(path))
        try:
            with open(path, 'w+') as f:
                f.write(json.dumps(self._facts))
        except:
            raise RuntimeError(
                "Netconify Error: can not write file, check directory persmissions")

    def _save_inventory_xml(self, savedir= os.getcwd(), no_save= True):
        if no_save is True:
            return
        if not hasattr(self._tty.nc.facts, 'inventory'):
            return
        fname = self._save_name + '-inventory.xml'
        path = os.path.join(savedir, fname)
        self._notify('inventory', 'saving: {0}'.format(path))
        as_xml = etree.tostring(
            self._tty.nc.facts.inventory, pretty_print=True)
        with open(path, 'w+') as f:
            f.write(as_xml)

    def _gather_facts(self):
        self._notify('facts', 'retrieving device facts...')
        self._tty.nc.facts.gather()
        self._facts = self._tty.nc.facts.items
        self.results['facts'] = self._facts
        self._save_name = self._hostname or self._facts[
            'hostname'] or '_'.join(self.console)

    def push_config(self, fname, action= 'merge'):
        """ push the configuration or rollback changes on error """
        if fname is not None and os.path.isfile(fname) is False:
            self.results['failed'] = True
            self.results[
                'errmsg'] = 'ERROR: unknown file: {0}'.format(fname)
            return self.results


        self._notify('conf', 'loading into device ...')
        content = open(fname, 'r').read()
        load_args = dict(content=content)
        load_args['action'] = action  # merge/replace; yeah, I know ...
        rc = self._tty.nc.load(**load_args)
        if rc is not True:
            self.results['failed'] = True
            self.results['errmsg'] = 'failure to load configuration, aborting.'
            self._notify('conf_ld_err', self.results['errmsg'])
            self._tty.nc.rollback()
            return

        self._notify('conf', 'commit ... please be patient')
        rc = self._tty.nc.commit()
        if rc is not True:
            self.results['failed'] = True
            self.results[
                'errmsg'] = 'faiure to commit configuration, aborting.'
            self._notify('conf_save_err', self.results['errmsg'])
            self._tty.nc.rollback()
            return
        self._notify('conf', 'commit completed.')
        self.results['changed'] = True
        return

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # -------------------------------------------------------------------------
    # QFX MODE processing
    # -------------------------------------------------------------------------
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    def _qfx_mode(self, mode):

        # ----------------------------------------------------
        # we need the facts, so if the caller didn't explicity
        # request them, grab them now
        # ----------------------------------------------------

        if self._facts is None:
            self._gather_facts()

        # --------------------------------------------------------
        # make sure we're logged into a QFX node device.
        # set this up as a list check in case we have other models
        # in the future to deal with.
        # --------------------------------------------------------

        if not any([self._facts['model'].startswith(m) for m in QFX_MODEL_LIST]):
            self.results['errmsg'] = "Not on a QFX device [{0}]".format(
                self._facts['model'])
            self.results['failed'] = True
            self._save_facts_json()
            self._save_inventory_xml()
            self.results['facts'] = self._facts
            self._notify('qfx', self.results['errmsg'])
            return

        now, later = self._qfx_device_mode_get()
        # compare to after-reoobt
        change = bool(later != mode)
        reboot = bool(now != mode)       # compare to now

        if now == QFX_MODE_SWITCH and change is True:   # flipping to NODE
            # --------------------------------------------------------
            # we want to revert the facts information from the 'FPC 0'
            # inventory, rather than the chassis, and re-save the facts
            # --------------------------------------------------------
            inv = self._tty.nc.facts.inventory
            fpc0 = inv.xpath('chassis/chassis-module[name="FPC 0"]')[0]
            self._facts['serialnumber'] = fpc0.findtext('serial-number')
            self._facts['model'] = fpc0.findtext('model-number')

        self._save_facts_json()
        self._save_inventory_xml()
        self.results['facts'] = self._facts

        self._notify('info', "QFX mode now/later: {0}/{1}".format(now, later))
        if now == later and later == mode:
            # nothing to do
            self._notify('info', 'No change required')
        else:
            self._notify('info', 'Action required')

        if change is True:
            self._notify('change',
                         'Changing the mode to: {0}'.format(mode))
            self.results['changed'] = True
            self._qfx_device_mode_set()

        if reboot is True:
            self._notify('change', 'REBOOTING device now!')
            self.results['changed'] = True
            self._tty.nc.reboot()
            # no need to close the tty, since the device is rebooting ...
            self._skip_logout = True

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # -------------------------------------------------------------------------
    # MISC device RPC commands & controls
    # -------------------------------------------------------------------------
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    # the following are the mode status string retrieved from NETCONF command
    # to determine the current mode

    _QFX_MODES = {
        'Standalone': QFX_MODE_SWITCH,
        'Node-device': QFX_MODE_NODE
    }

    # the following are the mode options inserted into the NETCONF command
    # to change the mode

    _QFX_XML_MODES = {
        QFX_MODE_SWITCH: 'standalone',
        QFX_MODE_NODE: 'node-device'
    }

    def _qfx_device_mode_get(self):
        """ get the current device mode """
        rpc = self._tty.nc.rpc
        got = rpc('show-chassis-device-mode')
        now = got.findtext('device-mode-current')
        later = got.findtext('device-mode-after-reboot')
        return (self._QFX_MODES[now], self._QFX_MODES[later])

    def _qfx_device_mode_set(self, mode):
        """ sets the device mode """
        rpc = self._tty.nc.rpc
        mode = self._QFX_XML_MODES[mode]
        cmd = '<request-chassis-device-mode><{0}/></request-chassis-device-mode>'.format(
            mode)
        got = rpc(cmd)
        return True

    # -----------------------------------------------------------------------
    # Context Manager
    # -----------------------------------------------------------------------

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
            if self.connected:
                self.close()