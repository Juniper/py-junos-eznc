from time import sleep
import logging

from jnpr.junos import exception as EzErrors
from jnpr.junos.transport.tty_netconf import tty_netconf

logger = logging.getLogger("jnpr.junos.tty")

__all__ = ["Terminal"]

# =========================================================================
# Terminal class
# =========================================================================


class Terminal(object):

    """
    Terminal is used to bootstrap Junos New Out of the Box (NOOB) device
    over the CONSOLE port. The general use-case is to setup the minimal
    configuration so that the device is IP reachable using SSH
    and NETCONF for remote management.

    Serial is needed for Junos devices that do not support
    the DHCP 'auto-installation' or 'ZTP' feature; i.e. you *MUST*
    do the NOOB configuration via the CONSOLE.

    Serial is also useful for situations even when the Junos
    device supports auto-DHCP, but is not an option due to the
    specific situation
    """

    TIMEOUT = 0.2  # serial readline timeout, seconds
    EXPECT_TIMEOUT = 10  # total read timeout, seconds
    LOGIN_RETRY = 20  # total number of passes thru login state-machine

    _ST_INIT = 0
    _ST_LOADER = 1
    _ST_LOGIN = 2
    _ST_PASSWD = 3
    _ST_DONE = 4
    _ST_BAD_PASSWD = 5
    _ST_TTY_NOLOGIN = 6
    _ST_TTY_OPTION = 7
    _ST_TTY_HOTKEY = 8

    _re_pat_login = r"(?P<login>ogin:\s*$)"

    _RE_PAT = [
        r"(?P<loader>oader>\s*$)",
        _re_pat_login,
        r"(?P<passwd>assword:\s*$)",
        "(?P<badpasswd>ogin incorrect)",
        r"(?P<netconf_closed><!-- session end at .*-->\s*)",
        r"(?P<shell>%|#|(~\$)\s*$)",
        '(?P<cli>[^\\-"]>\s*$)',
        r"(?P<option>Enter your option:\s*$)",
        "(?P<hotkey>connection: <CTRL>Z)",
    ]

    # -----------------------------------------------------------------------
    # CONSTRUCTOR
    # -----------------------------------------------------------------------

    def __init__(self, **kvargs):
        """
        :kvargs['user']:
          defaults to 'root'

        :kvargs['passwd']:
          defaults to empty; NOOB Junos device there is
          no root password initially

        :kvargs['attempts']:
          the total number of login attempts thru the login
          state-machine
        """
        # logic args
        self.hostname = self.__dict__.get("host")
        self.user = kvargs.get("user", "root")
        self.passwd = kvargs.get("passwd", "")
        self.cs_user = kvargs.get("cs_user")
        self.cs_passwd = kvargs.get("cs_passwd")
        self.login_attempts = kvargs.get("attempts") or self.LOGIN_RETRY
        self.console_has_banner = kvargs.get("console_has_banner") or False
        self._huge_tree = kvargs.get("huge_tree", False)

        # misc setup
        self.nc = tty_netconf(self)
        self.state = self._ST_INIT
        self._badpasswd = 0
        self._loader = 0

    @property
    def tty_name(self):
        return self._tty_name

    # -----------------------------------------------------------------------
    # Login/logout
    # -----------------------------------------------------------------------

    def login(self):
        """
        open the TTY connection and login.  once the login is successful,
        start the NETCONF XML API process
        """
        logger.info("TTY: connecting to TTY:{} ...".format(self.tty_name))
        self._tty_open()

        logger.info("TTY: logging in......")

        self.state = self._ST_INIT
        self._login_state_machine()

        # now start NETCONF XML
        logger.info("TTY: OK.....starting NETCONF")
        self.nc.open(at_shell=self.at_shell)
        self.session_id = self.nc._session_id

        return True

    def logout(self):
        """
        cleanly logout of the TTY
        """
        logger.info("logout: logging out.....")
        self.nc.close()
        self._logout_state_machine()
        return True

        # ---------------------------------------------------------------------
        # TTY logout state-machine
        # ---------------------------------------------------------------------

    def _logout_state_machine(self, attempt=0):
        if 10 == attempt:
            raise RuntimeError("logout_sm_failure")

        prompt, found = self.read_prompt()

        def _ev_login():
            # back at login prompt, so we are cleanly done!
            self._tty_close()

        def _ev_shell():
            self.write("exit")

        def _ev_cli():
            self.write("exit")

        # Connection closed by foreign host
        def _ev_netconf_closed():
            return True

        _ev_tbl = {
            "login": _ev_login,
            "shell": _ev_shell,
            "cli": _ev_cli,
            "netconf_closed": _ev_netconf_closed,
        }

        # hack for now
        # in case of telnet to management port, after writing exit on console
        # it exits completely and returns None
        ###
        if found is not None:
            _ev_tbl[found]()
        else:
            return True

        if found == "login":
            return True

        else:
            sleep(1)
            return self._logout_state_machine(attempt=attempt + 1)

    # -----------------------------------------------------------------------
    # TTY login state-machine
    # -----------------------------------------------------------------------
    def _login_state_machine(self, attempt=0):
        if self.login_attempts == attempt:
            raise RuntimeError("login_sm_failure")

        prompt, found = self.read_prompt()

        def _ev_loader():
            self.state = self._ST_LOADER
            self.write("boot")
            self.write("\n")
            sleep(300)
            self._login_state_machine(attempt=0)
            self._loader += 1
            if self._loader == 2:
                raise RuntimeError("probably corrupted image, stuck in loader")

        def _ev_login():
            self.state = self._ST_LOGIN
            self.write(self.user)

        def _ev_passwd():
            self.state = self._ST_PASSWD
            self.write(self.passwd)

        def _ev_bad_passwd():
            self.state = self._ST_BAD_PASSWD
            self.write("\n")
            self._badpasswd += 1
            if self._badpasswd == 2:
                # raise RuntimeError("Bad username/password")
                raise EzErrors.ConnectAuthError(self, "Bad username/password")
            # return through and try again ... could have been
            # prior failed attempt

        def _ev_tty_nologin():
            if self._ST_INIT == self.state:
                # assume we're in a hung state, i.e. we don't see
                # a login prompt for whatever reason
                self.state = self._ST_TTY_NOLOGIN
                # For console based telnet connection a new-line is required.
                # Code modified to check with a newline for telnet based connections.
                # Keeping below code as a comment for future enhancement.
                # if self.console_has_banner:
                # # if console connection has a banner or warning,
                # # use this hack
                #     sleep(5)
                #     self.write("\n")
                sleep(5)
                self.write("\n")
            else:
                # @@@ this is still a hack - used by default
                self.write("<close-session/>")

        def _ev_shell():
            if self.state == self._ST_INIT:
                # this means that the shell was left
                # open.  probably not a good thing,
                # so issue a logging message, but move on.
                logger.warning("login_warn: Shell login was open!!")

            self.at_shell = True
            self.state = self._ST_DONE
            # if we are here, then we are done

        def _ev_cli():
            if self.state == self._ST_INIT:
                # this means that the shell was left open.  probably not a
                # good thing, so issue a logging message, hit <ENTER> and try
                # again just to be sure...
                logger.warning("login_warn: waiting on TTY..... ")
                sleep(5)
                #  return

            self.at_shell = False
            self.state = self._ST_DONE

        def _ev_option():
            self.state = self._ST_TTY_OPTION
            self.write("1")

        def _ev_hot_key():
            self.state = self._ST_TTY_HOTKEY
            self.write("\n")

        _ev_tbl = {
            "loader": _ev_loader,
            "login": _ev_login,
            "passwd": _ev_passwd,
            "badpasswd": _ev_bad_passwd,
            "shell": _ev_shell,
            "cli": _ev_cli,
            "option": _ev_option,
            "hotkey": _ev_hot_key,
        }

        _ev_tbl.get(found, _ev_tty_nologin)()

        if self.state == self._ST_DONE:
            return True
        else:
            # if we are here, then loop the event again
            self._login_state_machine(attempt + 1)
