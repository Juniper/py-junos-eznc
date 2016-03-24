"""
This file defines the 'netconifyCmdo' class.
Used by the 'netconify' shell utility.
"""
import os
import json
import re
import argparse
from getpass import getpass
from lxml import etree
import traceback

from jnpr.junos.netconify import constants as C
from jnpr.junos.netconify.tty_telnet import Telnet
from jnpr.junos.netconify.tty_serial import Serial

# only export the netconifyCmdo class definition
__all__ = ['netconifyCmdo']

QFX_MODEL_LIST = ['QFX3500', 'QFX3600', 'VIRTUAL CHASSIS']
QFX_MODE_NODE = 'NODE'
QFX_MODE_SWITCH = 'SWITCH'


class netconifyCmdo(object):

    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------

    def __init__(self, **kvargs):
        """
        kvargs['notify']
          event notify callback
        """

        #
        # private attributes
        #
        self._name = None
        self._tty = None
        self._skip_logout = False
        self.on_notify = kvargs.get('notify', None)


        #
        # public attributes
        #
        self.facts = None
        self.results = dict(changed=False, failed=False, errmsg=None)



        self.host = kvargs.get('host')
        self.junos_conf_file = kvargs.get('junos_conf_file')
        self.junos_merge_conf = kvargs.get('junos_merge_conf', 'overwrite')
        self.qfx_mode = kvargs.get('qfx_mode')
        self.request_zeroize = kvargs.get('request_zeroize', False)
        self.request_shutdown = kvargs.get('request_shutdown', False)
        self.gather_facts = kvargs.get('gather_facts', False)
        self.request_srx_cluster = kvargs.get('request_srx_cluster')
        self.request_srx_cluster_dis = kvargs.get('request_srx_cluster_dis')
        self.savedir = kvargs.get('savedir')
        self.no_save = kvargs.get('no_save', False)
        self.port = kvargs.get('port','/dev/ttyUSB0')
        self.baud = kvargs.get('baud', '9600')
        self.mode = kvargs.get('mode', 'telnet')
        self.timeout = kvargs.get('timeout', '0.5')
        self.user = kvargs.get ('user', 'root')
        self.passwd = kvargs.get('password')
        self.attempts = kvargs.get('attempts', 10)
















    def _init_argsparser(self):
        p = argparse.ArgumentParser(add_help=True)
        self._argsparser = p

        # ---------------------------------------------------------------------
        # input identifiers
        # ---------------------------------------------------------------------

        p.add_argument('name',
                       nargs='?',
                       help='name of Junos device')

        p.add_argument('--version', action='version', version=C.version)

        # ---------------------------------------------------------------------
        # Device level options
        # ---------------------------------------------------------------------

        g = p.add_argument_group('DEVICE options')

        g.add_argument('-f', '--file',
                       dest='junos_conf_file',
                       help="Junos configuration file")

        g.add_argument("--merge",
                       dest='junos_merge_conf',
                       help='load-merge conf file, default is overwrite',
                       action='store_true')

        g.add_argument('--qfx-node',
                       dest='qfx_mode',
                       action='store_const', const=QFX_MODE_NODE,
                       help='Set QFX device into "node" mode')

        g.add_argument('--qfx-switch',
                       dest='qfx_mode',
                       action='store_const', const=QFX_MODE_SWITCH,
                       help='Set QFX device into "switch" mode')

        g.add_argument('--zeroize',
                       dest='request_zeroize',
                       action='store_true',
                       help='ZEROIZE the device')

        g.add_argument('--shutdown',
                       dest='request_shutdown',
                       choices=['poweroff', 'reboot'],
                       help='SHUTDOWN or REBOOT the device')

        g.add_argument('--facts',
                       action='store_true',
                       dest='gather_facts',
                       help='Gather facts and save them into SAVEDIR')

        g.add_argument('--srx_cluster',
                       dest='request_srx_cluster',
                       help='cluster_id,node ... Invoke cluster on SRX device and reboot')

        g.add_argument('--srx_cluster_disable',
                       dest='request_srx_cluster_dis',
                       action='store_true',
                       help='Disable cluster mode on SRX device and reboot')

        # ---------------------------------------------------------------------
        # directories
        # ---------------------------------------------------------------------

        g = p.add_argument_group('DIRECTORY options')

        g.add_argument('-S', '--savedir',
                       nargs='?', default='.',
                       help="Files are saved into this directory, $CWD by default")

        g.add_argument('--no-save',
                       action='store_true',
                       help="Do not save facts and inventory files")

        # ---------------------------------------------------------------------
        # console port
        # ---------------------------------------------------------------------

        g = p.add_argument_group('CONSOLE options')

        g.add_argument('-p', '--port',
                       default='/dev/ttyUSB0',
                       help="serial port device")

        g.add_argument('-b', '--baud',
                       default='9600',
                       help="serial port baud rate")

        g.add_argument('-t', '--telnet',
                       help='terminal server, <host>,<port>')

        g.add_argument('--timeout',
                       default='0.5',
                       help='TTY connection timeout (s)')

        # ---------------------------------------------------------------------
        # login configuration
        # ---------------------------------------------------------------------

        g = p.add_argument_group("LOGIN options")

        g.add_argument('-u', '--user',
                       default='root',
                       help='login user name, defaults to "root"')

        g.add_argument('-P', '--passwd',
                       default='',
                       help='login user password, *empty* for NOOB')

        g.add_argument('-k',
                       action='store_true', default=False,
                       dest='passwd_prompt',
                       help='prompt for user password')

        g.add_argument('-a', '--attempts',
                       default=10,
                       help='login attempts before giving up')

    # -------------------------------------------------------------------------
    # run command, can be involved from SHELL or programmatically
    # -------------------------------------------------------------------------

    def run(self):

        # ---------------------------------------------------------------
        # validate command options before going through the LOGIN process
        # ---------------------------------------------------------------

        fname = self.junos_conf_file
        if fname is not None:
            if os.path.isfile(fname) is False:
                self.results['failed'] = True
                self.results[
                    'errmsg'] = 'ERROR: unknown file: {0}'.format(fname)
                return self.results

        # --------------------
        # login to the CONSOLE
        # --------------------

        try:
            self._tty_login()
        except Exception as err:
            self._hook_exception('login', err)

        # ----------------------------------------------------
        # now deal with the various actions/options provided
        # by the command args
        # -----------------------------------------------------

        try:
            self._do_actions()
        except Exception as err:
            try:
                self._tty_logout()
            except Exception as logout_err:
                self._hook_exception('ERROR', "{0}\n".format(str(logout_err)))
            traceback.print_exc()
            self._hook_exception('action', err)

        # ----------------------------------------------------
        # logout, unless we don't need to (due to reboot,etc.)
        # -----------------------------------------------------

        if self._skip_logout is False:
            try:
                self._tty_logout()
            except Exception as err:
                self._hook_exception('logout', err)
        else:
            try:
                self._tty._tty_close()
            except Exception as err:
                self._hook_exception('close', err)

        return self.results

    # -------------------------------------------------------------------------
    # Handlers
    # -------------------------------------------------------------------------

    def _hook_exception(self, event, err):
        self._notify("ERROR", "{0}\n".format(str(err)))
        raise

    def _tty_notifier(self, tty, event, message):
        self._notify("TTY:{0}".format(event), message)

    def _notify(self, event, message):
        if self.on_notify is not None:
            self.on_notify(self, event, message)
        elif self.on_notify is not False:
            print "{0}:{1}".format(event, message)

    # -------------------------------------------------------------------------
    # LOGIN/LOGOUT
    # -------------------------------------------------------------------------

    def _tty_login(self):

        tty_args = {}
        tty_args['user'] = self.user
        tty_args['passwd'] = self.passwd
        tty_args['timeout'] = float(self.timeout)
        tty_args['attempts'] = int(self.attempts)

        if self.mode == 'telnet':
            tty_args['host'] = self.host
            tty_args['port'] = self.port
            self.console = ('telnet', self.host, self.port)
            self._tty = Telnet(**tty_args)
        else:
            tty_args['port'] = self.port
            tty_args['baud'] = self.baud
            self.console = ('serial', self.port)
            self._tty = Serial(**tty_args)

        notify = self.on_notify or self._tty_notifier
        self._tty.login(notify=notify)

    def _tty_logout(self):
        self._tty.logout()

    # -------------------------------------------------------------------------
    # ACTIONS
    # -------------------------------------------------------------------------
    def _do_actions(self):

        if self.request_srx_cluster is not None:
            self._srx_cluster()
            return

        if self.request_srx_cluster_dis:
            self._srx_cluster_disable()
            return

        if self.request_shutdown:
            self._shutdown()
            return

        if self.request_zeroize:
            print "\n zeroizing device ******"
            self._zeroize()
            return

        if self.gather_facts is True:
            print "\n ****** gather_facts ******"
            self._gather_facts()
            self._save_facts_json()
            self._save_inventory_xml()

        if self.junos_conf_file is not None:
            self._push_config()

        if self.qfx_mode is not None:
            self._qfx_mode()

    def _srx_cluster(self):
        """ Enable cluster mode on SRX device"""
        srx_args = {}
        cluster_id, node = re.split('[:,]', self.request_srx_cluster)
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
        self._notify('srx_cluster', 'disable cluster mode on srx device, rebooting')
        self._tty.nc.disablecluster()
        self._skip_logout = True
        self.results['changed'] = True

    def _zeroize(self):
        """ perform device ZEROIZE actions """
        self._notify('zeroize', 'ZEROIZE device, rebooting')
        self._tty.nc.zeroize()
        self._skip_logout = True
        self.results['changed'] = True

    def _shutdown(self):
        """ shutdown or reboot """
        self._skip_logout = True
        mode = self.request_shutdown
        self._notify('shutdown', 'shutdown {0}'.format(mode))
        nc = self._tty.nc
        shutdown = nc.poweroff if 'poweroff' == mode else nc.reboot
        shutdown()
        self._skip_logout = True
        self.results['changed'] = True

    def _save_facts_json(self):
        if self.no_save is True:
            return
        fname = self._save_name + '-facts.json'
        if self.savedir is None:
            fpath = os.getcwd()
        else:
            fpath = self.savedir
        path = os.path.join(fpath, fname)
        self._notify('facts', 'saving: {0}'.format(path))
        with open(path, 'w+') as f:
            f.write(json.dumps(self.facts))

    def _save_inventory_xml(self):
        if self.no_save is True:
            return
        if not hasattr(self._tty.nc.facts, 'inventory'):
            return

        fname = self._save_name + '-inventory.xml'
        if self.savedir is None:
            fpath = os.getcwd()
        else:
            fpath = self.savedir

        path = os.path.join(fpath, fname)
        self._notify('inventory', 'saving: {0}'.format(path))
        as_xml = etree.tostring(
            self._tty.nc.facts.inventory, pretty_print=True)
        with open(path, 'w+') as f:
            f.write(as_xml)

    def _gather_facts(self):
        self._notify('facts', 'retrieving device facts...')
        self._tty.nc.facts.gather()
        self.facts = self._tty.nc.facts.items
        self.results['facts'] = self.facts
        self._save_name = self._name or self.facts[
            'hostname'] or '_'.join(self.console)

    def _push_config(self):
        """ push the configuration or rollback changes on error """

        self._notify('conf', 'loading into device ...')
        content = open(self.junos_conf_file, 'r').read()
        load_args = dict(content=content)
        print "\n ****** inside push_config ****** \n"
        if self.junos_merge_conf is True:
            load_args['action'] = 'replace'  # merge/replace; yeah, I know ...
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
    def _qfx_mode(self):

        # ----------------------------------------------------
        # we need the facts, so if the caller didn't explicity
        # request them, grab them now
        # ----------------------------------------------------

        if self.facts is None:
            self._gather_facts()
        facts = self.facts  # alias

        # --------------------------------------------------------
        # make sure we're logged into a QFX node device.
        # set this up as a list check in case we have other models
        # in the future to deal with.
        # --------------------------------------------------------

        if not any([facts['model'].startswith(m) for m in QFX_MODEL_LIST]):
            self.results['errmsg'] = "Not on a QFX device [{0}]".format(
                facts['model'])
            self.results['failed'] = True
            self._save_facts_json()
            self._save_inventory_xml()
            self.results['facts'] = self.facts
            self._notify('qfx', self.results['errmsg'])
            return

        now, later = self._qfx_device_mode_get()
        # compare to after-reoobt
        change = bool(later != self.qfx_mode)
        reboot = bool(now != self.qfx_mode)       # compare to now

        if now == QFX_MODE_SWITCH and change is True:   # flipping to NODE
            # --------------------------------------------------------
            # we want to revert the facts information from the 'FPC 0'
            # inventory, rather than the chassis, and re-save the facts
            # --------------------------------------------------------
            inv = self._tty.nc.facts.inventory
            fpc0 = inv.xpath('chassis/chassis-module[name="FPC 0"]')[0]
            facts['serialnumber'] = fpc0.findtext('serial-number')
            facts['model'] = fpc0.findtext('model-number')

        self._save_facts_json()
        self._save_inventory_xml()
        self.results['facts'] = self.facts

        self._notify('info', "QFX mode now/later: {0}/{1}".format(now, later))
        if now == later and later == self.qfx_mode:
            # nothing to do
            self._notify('info', 'No change required')
        else:
            self._notify('info', 'Action required')

        if change is True:
            self._notify('change',
                         'Changing the mode to: {0}'.format(self.qfx_mode))
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

    def _qfx_device_mode_set(self):
        """ sets the device mode """
        rpc = self._tty.nc.rpc
        mode = self._QFX_XML_MODES[self.qfx_mode]
        cmd = '<request-chassis-device-mode><{0}/></request-chassis-device-mode>'.format(mode)
        got = rpc(cmd)
        return True
