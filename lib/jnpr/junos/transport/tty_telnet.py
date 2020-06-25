from time import sleep
import telnetlib
import logging
import sys
import six

from jnpr.junos.transport.tty import Terminal

logger = logging.getLogger("jnpr.junos.tty_telnet")

# -------------------------------------------------------------------------
# Terminal connection over TELNET CONSOLE
# -------------------------------------------------------------------------


class PY6:
    NEW_LINE = six.b("\n")
    EMPTY_STR = six.b("")
    NETCONF_EOM = six.b("]]>]]>")
    IN_USE = six.b("in use")


class Telnet(Terminal):
    RETRY_OPEN = 3  # number of attempts to open TTY
    RETRY_BACKOFF = 2  # seconds to wait between retries

    def __init__(self, host, port, **kvargs):
        """
        :host:
          The hostname or ip-addr of the terminal server

        :port:
          The TCP port that maps to the TTY device on the
          console server

        :kvargs['timeout']:
          this is the tty read polling timeout.
          generally you should not have to tweak this.
        """
        # initialize the underlying TTY device

        self._tn = telnetlib.Telnet()
        self._rx = self._tn
        self.host = host
        self.port = port
        self.timeout = kvargs.get("timeout", self.TIMEOUT)
        self.baud = kvargs.get("baud", 9600)
        self._tty_name = "{}:{}".format(host, port)

        Terminal.__init__(self, **kvargs)

    # -------------------------------------------------------------------------
    # I/O open close called from Terminal class
    # -------------------------------------------------------------------------

    def _tty_open(self):
        retry = self.RETRY_OPEN
        while retry > 0:
            try:
                self._tn.open(self.host, self.port, self.timeout)
                break
            except Exception:
                retry -= 1
                logger.info(
                    "TTY busy: checking back in {} ...".format(self.RETRY_BACKOFF)
                )
                sleep(self.RETRY_BACKOFF)
        else:
            raise RuntimeError("open_fail: port not ready")
        self.write("\n")

    def _tty_close(self):
        self._tn.close()

    # -------------------------------------------------------------------------
    # I/O read and write called from Terminal class
    # -------------------------------------------------------------------------

    def write(self, content):
        """ write content + <ENTER> """
        logger.debug("Write: %s" % content)
        self._tn.write(six.b((content + "\n")))

    def rawwrite(self, content):
        """ write content as-is """
        logger.debug("rawwrite: %s" % content)
        # If baud set to 0 write full speed
        if int(self.baud) == 0:
            self._tn.write(content)
            return None

        # Write data according to defined baud
        # per 1 byte of data there are 2 additional bits on the line
        # (parity and stop bits)
        if sys.version >= "3":
            content = content.decode("utf-8")
        for char in content:
            self._tn.write(six.b(char))
            wtime = 10 / float(self.baud)
            sleep(wtime)  # do not remove

    def read(self):
        """ read a single line """
        return self._tn.read_until(PY6.NEW_LINE, self.EXPECT_TIMEOUT)

    def read_prompt(self):
        _RE_PAT = [six.b(i) for i in Terminal._RE_PAT]
        got = self._tn.expect(_RE_PAT, self.EXPECT_TIMEOUT)
        if PY6.IN_USE in got[2]:
            raise RuntimeError("open_fail: port already in use")
        if len(got) >= 3:
            logger.debug("Got: %s" % got[2])
        return (None, None) if not got[1] else (got[2], got[1].lastgroup)
