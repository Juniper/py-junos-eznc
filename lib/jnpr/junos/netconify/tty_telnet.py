from time import sleep
import telnetlib

from jnpr.junos.netconify.tty import Terminal

# -------------------------------------------------------------------------
# Terminal connection over TELNET CONSOLE
# -------------------------------------------------------------------------


class Telnet(Terminal):
    RETRY_OPEN = 3                # number of attempts to open TTY
    RETRY_BACKOFF = 2             # seconds to wait between retries

    def __init__(self, host, port, **kvargs):
        print "\n ******* tty_telnet: init ******\n"
        """
        :host:
          The hostname or ip-addr of the ternminal server

        :port:
          The TCP port that maps to the TTY device on the
          console server

        :kvargs['timeout']:
          this is the tty read polling timeout.
          generally you should not have to tweak this.
        """
        # initialize the underlying TTY device

        self._tn = telnetlib.Telnet()
        self.host = host
        self.port = port
        self.timeout = kvargs.get('timeout', self.TIMEOUT)
        self._tty_name = "{0}:{1}".format(host, port)

        Terminal.__init__(self, **kvargs)

    # -------------------------------------------------------------------------
    # I/O open close called from Terminal class
    # -------------------------------------------------------------------------

    def _tty_open(self):
        print "\n ******* tty_telnet: _tty_open **********"
        retry = self.RETRY_OPEN
        while retry > 0:
            try:
                self._tn.open(self.host, self.port, self.timeout)
                break
            except Exception as err:
                retry -= 1
                self.notify("TTY busy", "checking back in {0} ...".format(self.RETRY_BACKOFF))
                sleep(self.RETRY_BACKOFF)
        else:
            raise RuntimeError("open_fail: port not ready")

        self.write('\n')

    def _tty_close(self):
        print "\n ******* tty_telnet: _tty_close ******\n"
        self._tn.close()

    # -------------------------------------------------------------------------
    # I/O read and write called from Terminal class
    # -------------------------------------------------------------------------

    def write(self, content):
        print "\n ******* tty_telnet: write ******\n"
        """ write content + <ENTER> """
        self._tn.write(content + '\n')

    def rawwrite(self, content):
        #print "\n ******* tty_telnet: rawwrite *****, content is: \n ", content
        """ write content as-is """
        self._tn.write(content)

    def read(self):
        print "\n ******* tty_telnet: read ******* \n "
        """ read a single line """
        return self._tn.read_until('\n', self.EXPECT_TIMEOUT)

    def read_prompt(self):
        print "\n *********** tty_telnet: read_prompt ****** \n"
        got = self._tn.expect(Terminal._RE_PAT, self.EXPECT_TIMEOUT)
        #print "\n got *****:", got
        sre = got[1]

        if 'in use' in got[2]:
            raise RuntimeError("open_fail: port already in use")

        # (buffer, RE group)
        return (None, None) if not got[1] else (got[2], got[1].lastgroup)