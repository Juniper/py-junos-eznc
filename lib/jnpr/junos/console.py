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
from jnpr.junos import Device
from jnpr.junos.facts import *
import logging

QFX_MODEL_LIST = ['QFX3500', 'QFX3600', 'VIRTUAL CHASSIS']
QFX_MODE_NODE = 'NODE'
QFX_MODE_SWITCH = 'SWITCH'

logger = logging.getLogger("jnpr.junos.console")
#logging.basicConfig(level=logging.INFO)

class Console(object):

    def __init__(self, host, **kvargs):
        """
        NoobDevice object constructor.

        :param str host:
            **REQUIRED** host-name or ipaddress of target device

        :param str user:
            *OPTIONAL* login user-name, uses root if not provided

        :param str passwd:
            *OPTIONAL* in console connection for device at zeroized state password is not required

        :param int port:
            *OPTIONAL*  port, default is telnet port `23`

        :param int baud:
            *OPTIONAL*  baud, default baud rate is 9600

        :param str mode:
            *OPTIONAL*  mode, mode of connection (telnet/serial/ssh)
            default is telnet

        :param int timeout:
            *OPTIONAL*  timeout, default is 0.5

        :param int attempts:
            *OPTIONAL*  attempts, default is 10

        :param str ssh_config:
            *OPTIONAL* The path to the SSH configuration file.
            This can be used to load SSH information from a configuration file.
            By default ~/.ssh/config is queried it will be used by SCP class.
            So its assumed ssh is enabled by the time we use SCP functionality.

        :param bool gather_facts:
            *OPTIONAL* default is ``False``.  If ``False`` then the
            facts are not gathered on call to :meth:`open`

        """

        # ----------------------------------------
        # setup instance connection/open variables
        # ----------------------------------------

        self._tty = None
        self._facts = {}
        self.connected = False
        self._skip_logout = False
        self.results = dict(changed=False, failed=False, errmsg=None)

        self._hostname = host
        self._auth_user = kvargs.get('user', 'root')
        self._auth_password = kvargs.get('password', '') or kvargs.get('passwd', '')
        self._port = kvargs.get('port', '23')
        self._baud = kvargs.get('baud', '9600')
        self._mode = kvargs.get('mode', 'telnet')
        self._timeout = kvargs.get('timeout', '0.5')
        self._attempts = kvargs.get('attempts', 10)
        self.gather_facts = kvargs.get('gather_facts', False)
        self.rpc = _RpcMetaExec(self)
        self.cli = lambda cmd, format='text', warning=True: \
            Device.cli.im_func(self, cmd, format, warning)
        self._ssh_config = kvargs.get('ssh_config')
        self._sshconf_path = Device._sshconf_lkup.im_func(self)

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
            logger.error("ERROR {0}:{1}\n".format('login', str(err)))
            logger.error("Complete traceback message: {0}".format(traceback.format_exc()))
            raise RuntimeError
        self.connected = True
        if self.gather_facts is True:
            self._gather_facts()
        return self

    def close(self, skip_logout = False):
        """
        Closes the connection to the device.
        """
        if skip_logout is False and self.connected is True:
            try:
                self._tty_logout()
            except Exception as err:
                logger.error("ERROR {0}:{1}\n".format('logout', str(err)))
            self.connected = False
        elif self.connected is True:
            try:
                self._tty._tty_close()
            except Exception as err:
                logger.error("ERROR {0}:{1}\n".format('close', str(err)))
                traceback.print_exc()
            self.connected = False

    # execute rpc calls
    def execute(self, rpc_cmd):
        return self._tty.nc.rpc(etree.tounicode(rpc_cmd))

    # -------------------------------------------------------------------------
    # LOGIN/LOGOUT
    # -------------------------------------------------------------------------

    def _tty_login(self):
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

        self._tty.login()

    def _tty_logout(self):
        self._tty.logout()


    def srx_cluster(self, cluster_id, node):
        """ Enable cluster mode on SRX device"""
        srx_args = {}
        srx_args['cluster_id'] = cluster_id
        srx_args['node'] = node
        logger.debug("{0}:{1}".format('srx_cluster', 'set device to cluster mode, rebooting'))
        logger.debug("srx_cluster: Cluster ID: {0}".format(cluster_id))
        logger.debug("srx_cluster: Node: {0}".format(node))
        self._tty.nc.enablecluster(cluster_id, node)
        self._skip_logout = True
        self.results['changed'] = True

    def srx_cluster_disable(self):
        """ Disable cluster mode on SRX device"""
        logger.debug ('srx_cluster:disable cluster mode on srx device, rebooting')
        self._tty.nc.disablecluster()
        self._skip_logout = True
        self.results['changed'] = True

    def zeroize(self):
        """ perform device ZEROIZE actions """
        logger.debug("zeroize : ZEROIZE device, rebooting")
        self._tty.nc.zeroize()
        self._skip_logout = True
        self.results['changed'] = True

    def _gather_facts(self):
        logger.debug('facts: retrieving device facts...')
        for gather in FACT_LIST:
            gather(self, self._facts)
        self.results['facts'] = self._facts

    """
    def push_config(self, fname, action= 'merge'):
        #push the configuration or rollback changes on error
        if fname is not None and os.path.isfile(fname) is False:
            self.results['failed'] = True
            self.results[
                'errmsg'] = 'ERROR: unknown file: {0}'.format(fname)
            return self.results
        logger.info("conf: loading into device....")
        content = open(fname, 'r').read()
        load_args = dict(content=content)
        load_args['action'] = action  # merge/replace; yeah, I know ...
        rc = self._tty.nc.load(**load_args)
        if rc is not True:
            self.results['failed'] = True
            self.results['errmsg'] = 'failure to load configuration, aborting.'
            logger.error('conf_ld_err: {0}'.format(self.results['errmsg']))
            self._tty.nc.rollback()
            return
        logger.info('conf:  commit ... please be patient')
        rc = self._tty.nc.commit()
        if rc is not True:
            self.results['failed'] = True
            self.results[
                'errmsg'] = 'faiure to commit configuration, aborting.'
            logger.error('conf_save_err: {0}'.format(self.results['errmsg']))
            self._tty.nc.rollback()
            return
        logger.info('conf,  commit completed')
        self.results['changed'] = True
        return
    """
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # -------------------------------------------------------------------------
    # QFX MODE processing
    # -------------------------------------------------------------------------
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    def qfx_mode(self, mode):

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
            self.results['facts'] = self._facts
            logger.error('qfx: {0}'.format((self.results['errmsg'])))
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
        self.results['facts'] = self._facts
        logger.debug("QFX mode now/later: {0}/{1}".format(now, later))
        if now == later and later == mode:
            # nothing to do
            logger.debug('No change required')
        else:
            logger.debug('Action required')

        if change is True:
            logger.debug('Change: Changing the mode to: {0}'.format(mode))
            self.results['changed'] = True
            self._qfx_device_mode_set()

        if reboot is True:
            logger.debug('Change: REBOOTING device now!')
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
