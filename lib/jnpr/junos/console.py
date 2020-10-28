import traceback
import sys
import logging
import warnings
import socket

# 3rd-party packages
from ncclient.devices.junos import JunosDeviceHandler
from lxml import etree
from jnpr.junos.transport.tty_telnet import Telnet
from jnpr.junos.transport.tty_serial import Serial
from jnpr.junos.transport.tty_ssh import SSH
from ncclient.xml_ import NCElement
from jnpr.junos.device import _Connection

# local modules
from jnpr.junos.rpcmeta import _RpcMetaExec
from jnpr.junos.factcache import _FactCache
from jnpr.junos import jxml as JXML
from jnpr.junos.ofacts import *
from jnpr.junos.decorators import ignoreWarnDecorator
from jnpr.junos.device import _Jinja2ldr

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
            *OPTIONAL* Defaults to ``False``. If ``False`` and old-style fact
            gathering is in use then facts are not gathered on call to
            :meth:`open`. This argument is a no-op when new-style fact
            gathering is in use (the default.)

        :param str fact_style:
            *OPTIONAL*  The style of fact gathering to use. Valid values are:
            'new', 'old', or 'both'. The default is 'new'. The value 'both' is
            only present for debugging purposes. It will be removed in a future
            release. The value 'old' is only present to workaround bugs in
            new-style fact gathering. It will be removed in a future release.

        :param bool console_has_banner:
            *OPTIONAL* default is ``False``.  If ``False`` then in case of a
            hung state, <close-session/> rpc is sent to the console.
            If ``True``, after sleep(5), a new-line is sent

        """

        # ----------------------------------------
        # setup instance connection/open variables
        # ----------------------------------------

        self._tty = None
        self._ofacts = {}
        self.connected = False
        self._skip_logout = False
        self.results = dict(changed=False, failed=False, errmsg=None)

        # hostname is not required in serial mode connection
        self._hostname = kvargs.get("host")
        self._auth_user = kvargs.get("user", "root")
        self._conf_auth_user = None
        self._conf_ssh_private_key_file = None
        self._auth_password = kvargs.get("password", "") or kvargs.get("passwd", "")
        self.cs_user = kvargs.get("cs_user")
        self.cs_passwd = kvargs.get("cs_passwd")
        self._port = kvargs.get("port", "22" if self.cs_user else "23")
        self._mode = kvargs.get("mode", None if self.cs_user else "telnet")
        self._baud = kvargs.get("baud", "9600")
        if self._hostname:
            self._ssh_config = kvargs.get("ssh_config")
            self._sshconf_lkup()
        self._ssh_private_key_file = (
            kvargs.get("ssh_private_key_file") or self._conf_ssh_private_key_file
        )
        self._timeout = kvargs.get("timeout", "0.5")
        self._normalize = kvargs.get("normalize", False)
        self._attempts = kvargs.get("attempts", 10)
        self._gather_facts = kvargs.get("gather_facts", False)
        self._fact_style = kvargs.get("fact_style", "new")
        self._huge_tree = kvargs.get("huge_tree", False)
        if self._fact_style != "new":
            warnings.warn(
                "fact-style %s will be removed in "
                "a future release." % (self._fact_style),
                RuntimeWarning,
            )
        self.console_has_banner = kvargs.get("console_has_banner", False)
        self.rpc = _RpcMetaExec(self)
        self._manages = []
        self.junos_dev_handler = JunosDeviceHandler(
            device_params={"name": "junos", "local": False}
        )
        self._conn = None
        self._j2ldr = _Jinja2ldr
        if self._fact_style == "old":
            self.facts = self.ofacts
        else:
            self.facts = _FactCache(self)

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

    @property
    def transform(self):
        """
        :returns: the current RPC XML Transformation.
        """
        return self.junos_dev_handler.transform_reply

    @transform.setter
    def transform(self, func):
        """
        Used to change the RPC XML Transformation.

        :param lambda value:
            New transform lambda
        """
        self.junos_dev_handler.transform_reply = func

    def open(self, *vargs, **kvargs):
        """
        Opens a connection to the device using existing login/auth
        information.

        :param bool gather_facts:
            If set to ``True``/``False`` will override the device
            instance value for only this open process
        """

        # ---------------------------------------------------------------
        # validate device hostname or IP address
        # ---------------------------------------------------------------
        if (
            (self._mode and self._mode.upper() == "TELNET") or self.cs_user is not None
        ) and self._hostname is None:
            self.results["failed"] = True
            self.results["errmsg"] = "ERROR: Device hostname/IP not specified !!!"
            return self.results

        # ---------------------------------------------------------------
        # validate console server and password. Password-less connection
        # is not supported
        # ---------------------------------------------------------------
        if self.cs_user is not None and self.cs_passwd is None:
            self.results["failed"] = True
            self.results["errmsg"] = (
                "ERROR: Console SSH, Password-less connection is " "not supported !!!"
            )
            logger.error(self.results["errmsg"])
            return self.results

        # --------------------
        # login to the CONSOLE
        # --------------------
        try:
            self._tty_login()
        except RuntimeError as err:
            logger.error("ERROR:  {}:{}\n".format("login", str(err)))
            logger.error(
                "\nComplete traceback message: {}".format(traceback.format_exc())
            )
            raise err
        except Exception as ex:
            logger.error("Exception occurred: {}:{}\n".format("login", str(ex)))
            raise ex
        self.connected = True

        self._nc_transform = self.transform
        self._norm_transform = lambda: JXML.normalize_xslt.encode("UTF-8")

        # normalize argument to open() overrides normalize argument value
        # to __init__(). Save value to self._normalize where it is used by
        # normalizeDecorator()
        self._normalize = kvargs.get("normalize", self._normalize)
        if self._normalize is True:
            self.transform = self._norm_transform

        gather_facts = kvargs.get("gather_facts", self._gather_facts)
        if gather_facts is True:
            logger.info("facts: retrieving device facts...")
            self.facts_refresh()
            self.results["facts"] = self.facts
        self._conn = self._tty
        return self

    def close(self, skip_logout=False):
        """
        Closes the connection to the device.
        """
        if skip_logout is False and self.connected is True:
            try:
                self._tty_logout()
            except socket.error as err:
                # if err contains "Connection reset by peer" connection to the
                # device got closed
                if "Connection reset by peer" not in str(err):
                    raise err
            except EOFError as err:
                if "telnet connection closed" not in str(err):
                    raise err
            except Exception as err:
                logger.error("ERROR {}:{}\n".format("logout", str(err)))
                raise err
            self.connected = False
        elif self.connected is True:
            try:
                self._tty._tty_close()
            except Exception as err:
                logger.error("ERROR {}:{}\n".format("close", str(err)))
                logger.error(
                    "\nComplete traceback message: {}".format(traceback.format_exc())
                )
                raise err
            self.connected = False

    @ignoreWarnDecorator
    def _rpc_reply(self, rpc_cmd_e, *args, **kwargs):
        encode = None if sys.version < "3" else "unicode"
        rpc_cmd = (
            etree.tostring(rpc_cmd_e, encoding=encode)
            if isinstance(rpc_cmd_e, etree._Element)
            else rpc_cmd_e
        )
        reply = self._tty.nc.rpc(rpc_cmd)
        rpc_rsp_e = NCElement(
            reply, self.junos_dev_handler.transform_reply(), self._huge_tree
        )._NCElement__doc
        return rpc_rsp_e

    # -------------------------------------------------------------------------
    # LOGIN/LOGOUT
    # -------------------------------------------------------------------------

    def _tty_login(self):
        tty_args = dict()
        tty_args["user"] = self._auth_user
        tty_args["passwd"] = self._auth_password
        tty_args["timeout"] = float(self._timeout)
        tty_args["attempts"] = int(self._attempts)
        tty_args["baud"] = self._baud
        tty_args["huge_tree"] = self._huge_tree
        if self._mode and self._mode.upper() == "TELNET":
            tty_args["host"] = self._hostname
            tty_args["port"] = self._port
            tty_args["console_has_banner"] = self.console_has_banner
            self.console = ("telnet", self._hostname, self.port)
            self._tty = Telnet(**tty_args)
        elif self.cs_user is not None:
            tty_args["cs_user"] = self.cs_user
            tty_args["cs_passwd"] = self.cs_passwd
            tty_args["host"] = self._hostname
            tty_args["port"] = self._port
            tty_args["console_has_banner"] = self.console_has_banner
            tty_args["ssh_private_key_file"] = self._ssh_private_key_file
            self.console = ("ssh", self._hostname, self.port)
            self._tty = SSH(**tty_args)
        elif self._mode.upper() == "SERIAL":
            tty_args["port"] = self._port
            self.console = ("serial", self._port)
            self._tty = Serial(**tty_args)
        else:
            logger.error("Mode should be either telnet or serial")
            raise AttributeError("Mode to be telnet/serial")

        self._tty.login()

    def _tty_logout(self):
        self._tty.logout()

    def zeroize(self):
        """ perform device ZEROIZE actions """
        logger.info("zeroize : ZEROIZE device, rebooting")
        self._tty.nc.zeroize()
        self._skip_logout = True
        self.results["changed"] = True

    # -----------------------------------------------------------------------
    # Context Manager
    # -----------------------------------------------------------------------

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connected:
            self.close()
