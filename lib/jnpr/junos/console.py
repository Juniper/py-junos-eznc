"""
This file defines the 'netconifyCmdo' class.
Used by the 'netconify' shell utility.
"""
import traceback
import sys
import logging
import warnings

# 3rd-party packages
import ncclient.transport.errors as NcErrors
import ncclient.operations.errors as NcOpErrors
from ncclient.devices.junos import JunosDeviceHandler
from lxml import etree
from jnpr.junos.transport.tty_telnet import Telnet
from jnpr.junos.transport.tty_serial import Serial
from ncclient.operations.rpc import RPCReply, RPCError
from ncclient.xml_ import NCElement
from jnpr.junos.device import _Connection

# local modules
from jnpr.junos.rpcmeta import _RpcMetaExec
from jnpr.junos import exception as EzErrors
from jnpr.junos.facts import *
from jnpr.junos import jxml as JXML
from jnpr.junos.decorators import timeoutDecorator, normalizeDecorator

QFX_MODEL_LIST = ['QFX3500', 'QFX3600', 'VIRTUAL CHASSIS']
QFX_MODE_NODE = 'NODE'
QFX_MODE_SWITCH = 'SWITCH'

logger = logging.getLogger("jnpr.junos.console")


class Console(_Connection):

    def __init__(self, **kvargs):
        """
        NoobDevice object constructor.

        :param str host:
            **REQUIRED** host-name or ipaddress of target device

        :param str user:
            *OPTIONAL* login user-name, uses root if not provided

        :param str passwd:
            *OPTIONAL* in console connection for device at zeroized state
            password is not required

        :param int port:
            *OPTIONAL*  port, defaults to '23' for telnet mode and
            '/dev/ttyUSB0' for serial.

        :param int baud:
            *OPTIONAL*  baud, default baud rate is 9600

        :param str mode:
            *OPTIONAL*  mode, mode of connection (telnet/serial)
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

        # hostname is not required in serial mode connection
        self._hostname = kvargs.get('host')
        self._auth_user = kvargs.get('user', 'root')
        self._auth_password = kvargs.get(
            'password',
            '') or kvargs.get(
            'passwd',
            '')
        self._port = kvargs.get('port', '23')
        self._baud = kvargs.get('baud', '9600')
        self._mode = kvargs.get('mode', 'telnet')
        self._timeout = kvargs.get('timeout', '0.5')
        self._normalize = kvargs.get('normalize', False)
        self._norm_transform = lambda: JXML.normalize_xslt.encode('UTF-8')
        self.transform = self._norm_transform
        # self.timeout needed by PyEZ utils
        #self.timeout = self._timeout
        self._attempts = kvargs.get('attempts', 10)
        self.gather_facts = kvargs.get('gather_facts', False)
        self.rpc = _RpcMetaExec(self)
        self._ssh_config = kvargs.get('ssh_config')
        self._manages = []
        self.junos_dev_handler = JunosDeviceHandler(device_params=
                                                    {'name': 'junos',
                                                     'local': False})

    @property
    def timeout(self):
        """
        :returns: current console connection timeout value (int) in seconds.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        """
        Used to change the console connection timeout value (default=0.5 sec).

        :param int value:
            New timeout value in seconds
        """
        self._timeout = value

    def open(self):
        """
        open the connection to the device
        """

        # ---------------------------------------------------------------
        # validate device hostname or IP address
        # ---------------------------------------------------------------
        if self._mode.upper() == 'TELNET' and self._hostname is None:
            self.results['failed'] = True
            self.results[
                'errmsg'] = 'ERROR: Device hostname/IP not specified !!!'
            return self.results

        # --------------------
        # login to the CONSOLE
        # --------------------
        try:
            self._tty_login()
        except RuntimeError as err:
            logger.error("ERROR:  {0}:{1}\n".format('login', str(err)))
            logger.error(
                "\nComplete traceback message: {0}".format(
                    traceback.format_exc()))
            raise err
        except Exception as ex:
            logger.error("Exception occurred: {0}:{1}\n".format('login', str(ex)))
            raise ex
        self.connected = True
        if self.gather_facts is True:
            logger.info('facts: retrieving device facts...')
            self.facts_refresh()
            self.results['facts'] = self._facts
        return self

    def close(self, skip_logout=False):
        """
        Closes the connection to the device.
        """
        if skip_logout is False and self.connected is True:
            try:
                self._tty_logout()
            except Exception as err:
                logger.error("ERROR {0}:{1}\n".format('logout', str(err)))
                raise err
            self.connected = False
        elif self.connected is True:
            try:
                self._tty._tty_close()
            except Exception as err:
                logger.error("ERROR {0}:{1}\n".format('close', str(err)))
                logger.error(
                    "\nComplete traceback message: {0}".format(
                        traceback.format_exc()))
                raise err
            self.connected = False

    def _rpc_reply(self, rpc_cmd_e):
        encode = None if sys.version < '3' else 'unicode'
        rpc_cmd = etree.tostring(rpc_cmd_e, encoding=encode) if \
                isinstance(rpc_cmd_e, etree._Element) else rpc_cmd_e
        reply = self._tty.nc.rpc(rpc_cmd)
        rpc_rsp_e = NCElement(reply, self.junos_dev_handler.transform_reply())._NCElement__doc
        return rpc_rsp_e

    # -------------------------------------------------------------------------
    # LOGIN/LOGOUT
    # -------------------------------------------------------------------------

    def _tty_login(self):
        tty_args = dict()
        tty_args['user'] = self._auth_user
        tty_args['passwd'] = self._auth_password
        tty_args['timeout'] = float(self._timeout)
        tty_args['attempts'] = int(self._attempts)
        tty_args['baud'] = self._baud
        if self._mode.upper() == 'TELNET':
            tty_args['host'] = self._hostname
            tty_args['port'] = self._port
            self.console = ('telnet', self._hostname, self.port)
            self._tty = Telnet(**tty_args)
        elif self._mode.upper() == 'SERIAL':
            tty_args['port'] = self._port
            self.console = ('serial', self._port)
            self._tty = Serial(**tty_args)
        else:
            logger.error('Mode should be either telnet or serial')
            raise AttributeError('Mode to be telnet/serial')

        self._tty.login()

    def _tty_logout(self):
        self._tty.logout()

    def zeroize(self):
        """ perform device ZEROIZE actions """
        logger.info("zeroize : ZEROIZE device, rebooting")
        self._tty.nc.zeroize()
        self._skip_logout = True
        self.results['changed'] = True

    # -----------------------------------------------------------------------
    # Context Manager
    # -----------------------------------------------------------------------

    def __enter__(self):
        self._conn = self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connected:
            self.close()
