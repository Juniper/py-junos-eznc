import serial
import re
import six
from time import sleep
from datetime import datetime, timedelta

from jnpr.junos.transport.tty import Terminal

# -------------------------------------------------------------------------
# Terminal connection over SERIAL CONSOLE
# -------------------------------------------------------------------------

_PROMPT = re.compile(six.b('|').join([six.b(i) for i in Terminal._RE_PAT]))


class Serial(Terminal):

    def __init__(self, port='/dev/ttyUSB0', **kvargs):
        """
        :port:
          the serial port, defaults to USB0 since this

        :kvargs['timeout']:
          this is the tty read polling timeout.
          generally you should not have to tweak this.
        """
        # initialize the underlying TTY device

        self.port = port
        self._ser = serial.Serial()
        self._rx = self._ser
        self._ser.port = port
        self._ser.timeout = kvargs.get('timeout', self.TIMEOUT)

        self._tty_name = self.port

        Terminal.__init__(self, **kvargs)

    # -------------------------------------------------------------------------
    # I/O open close called from Terminal class
    # -------------------------------------------------------------------------

    def _tty_open(self):
        try:
            self._ser.open()
        except OSError as err:
            raise RuntimeError("open_failed:{0}".format(err.strerror))
        self.write('\n\n\n')      # hit <ENTER> a few times, yo!

    def _tty_close(self):
        self._ser.flush()
        self._ser.close()

    # -------------------------------------------------------------------------
    # I/O read and write called from Terminal class
    # -------------------------------------------------------------------------

    def write(self, content):
        """ write content + <RETURN> """
        self._ser.write(six.b(content + '\n'))
        self._ser.flush()

    def rawwrite(self, content):
        self._ser.write(content)

    def read(self):
        """ read a single line """
        return self._ser.readline()

    def read_prompt(self):
        """
        reads text from the serial console (using readline) until
        a match is found against the :expect: regular-expression object.
        When a match is found, return a tuple(<text>,<found>) where
        <text> is the complete text and <found> is the name of the
        regular-expression group. If a timeout occurs, then return
        the tuple(None,None).
        """
        rxb = six.b('')
        mark_start = datetime.now()
        mark_end = mark_start + timedelta(seconds=self.EXPECT_TIMEOUT)

        while datetime.now() < mark_end:
            sleep(0.1)                          # do not remove
            line = self._ser.readline()
            if not line:
                continue
            rxb += line
            found = _PROMPT.search(rxb)
            if found is not None:
                break         # done reading
        else:
            # exceeded the while loop timeout
            return (None, None)

        return (rxb, found.lastgroup)
