import logging
import re
import select
import socket
import sys
from time import sleep, time

import paramiko
import six

from jnpr.junos.transport.tty import Terminal

logger = logging.getLogger("jnpr.junos.tty_ssh")

# -------------------------------------------------------------------------
# Terminal connection over SSH CONSOLE
# -------------------------------------------------------------------------
_PROMPT = re.compile(six.b("|").join([six.b(i) for i in Terminal._RE_PAT]))


class PY6:
    NEW_LINE = six.b("\n")
    EMPTY_STR = six.b("")
    NETCONF_EOM = six.b("]]>]]>")
    IN_USE = six.b("in use")


class SSH(Terminal):
    RETRY_OPEN = 3  # number of attempts to open TTY
    RETRY_BACKOFF = 2  # seconds to wait between retries
    MAX_BUFFER = 65535
    READ_PROMPT_DELAY = 10.0
    RECVSZ = 1024

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

        self._ssh_pre = self._ssh_client_pre()
        self.host = host
        self.port = port
        self.ssh_private_key_file = kvargs.get("ssh_private_key_file")
        self.timeout = kvargs.get("timeout", self.TIMEOUT)
        self.baud = kvargs.get("baud", 9600)
        self._tty_name = "{}:{}".format(host, port)

        Terminal.__init__(self, **kvargs)

    @staticmethod
    def _ssh_client_pre():
        ssh_client_pre = paramiko.SSHClient()
        ssh_client_pre.load_system_host_keys()
        ssh_client_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        return ssh_client_pre

    # -------------------------------------------------------------------------
    # I/O open close called from Terminal class
    # -------------------------------------------------------------------------

    def _tty_open(self):
        retry = self.RETRY_OPEN

        # we want to enable the ssh-agent if-and-only-if we are
        # not given a password or an ssh key file.
        # in this condition it means we want to query the agent
        # for available ssh keys
        allow_agent = bool(
            (self.cs_passwd is None) and (self.ssh_private_key_file is None)
        )

        while retry > 0:
            try:
                self._ssh_pre.connect(
                    hostname=self.host,
                    port=int(self.port),
                    username=self.cs_user,
                    password=self.cs_passwd,
                    timeout=self.timeout,
                    allow_agent=allow_agent,
                    look_for_keys=False,
                    key_filename=self.ssh_private_key_file,
                )
                break
            except socket.error as err:
                retry -= 1
                logger.error(
                    "SSH Socket Error: {}. Checking back in: {}".format(
                        str(err), self.RETRY_BACKOFF
                    )
                )
                sleep(self.RETRY_BACKOFF)
            except paramiko.BadHostKeyException as err:
                retry -= 1
                logger.error(
                    "SSH Bad Host Key Error: {}.Checking back in: {}".format(
                        str(err), self.RETRY_BACKOFF
                    )
                )
                sleep(self.RETRY_BACKOFF)
            except paramiko.AuthenticationException as err:
                retry -= 1
                logger.error(
                    "SSH Auth Error: {}. Checking back in: {}".format(
                        str(err), self.RETRY_BACKOFF
                    )
                )
                sleep(self.RETRY_BACKOFF)
        else:
            raise RuntimeError("open_fail: port not ready")

        self._ssh = self._ssh_pre.invoke_shell()
        self._ssh.read_until = self._read_until
        self._rx = self._ssh
        self.write("\n")

    def _tty_close(self):
        self._ssh_pre.close()
        del self._ssh_pre

    # -------------------------------------------------------------------------
    # I/O read and write called from Terminal class
    # -------------------------------------------------------------------------

    def write(self, content):
        """write content + <ENTER>"""
        logger.debug("Write: %s" % content)
        self._ssh.sendall(six.b((content + "\n")))

    def rawwrite(self, content):
        """write content as-is"""
        logger.debug("rawwrite: %s" % content)
        # If baud set to 0 write full speed
        if int(self.baud) == 0:
            self._ssh.sendall(content)
            return None

        # Write data according to defined baud
        # per 1 byte of data there are 2 additional bits on the line
        # (parity and stop bits)
        if sys.version >= "3":
            content = content.decode("utf-8")
        for char in content:
            self._ssh.sendall(six.b(char))
            wtime = 10 / float(self.baud)
            sleep(wtime)  # do not remove

    def read(self):
        """read a single line"""
        rxb = six.b("")
        while True:
            data = self._ssh.recv(self.RECVSZ)
            if data is None or len(data) <= 0:
                raise ValueError("Unable to detect device prompt")
            elif PY6.NEW_LINE in data:
                rxb += data.split(PY6.NEW_LINE)[0]
                break
            else:
                rxb += data

        return rxb

    def read_prompt(self):
        """
        reads text from the serial console (using paramiko recv) until
        a match is found against the :expect: regular-expression object.
        When a match is found, return a tuple(<text>,<found>) where
        <text> is the complete text and <found> is the name of the
        regular-expression group. If a timeout occurs, then return
        the tuple(None,None).
        """
        rxb = six.b("")
        timeout = time() + self.READ_PROMPT_DELAY

        while time() < timeout:
            sleep(0.1)
            rd, _, _ = select.select([self._ssh], [], [], 0.1)
            sleep(0.05)
            if rd:
                rxb += self._ssh.recv(self.RECVSZ)
                found = _PROMPT.search(rxb)
                if found is not None:
                    break
                timeout = time() + self.READ_PROMPT_DELAY
        else:
            return None, None
        logger.debug("Got: %s" % rxb)
        return rxb, found.lastgroup

    def _read_until(self, match, timeout=None):
        rxb = six.b("")
        timeout = time() + self.READ_PROMPT_DELAY

        while time() < timeout:
            sleep(0.1)
            rd, _, _ = select.select([self._ssh], [], [], 0.1)
            sleep(0.05)
            if rd:
                rxb += self._ssh.recv(self.MAX_BUFFER)
                if re.search(match, rxb):
                    return rxb

                timeout = time() + self.READ_PROMPT_DELAY
