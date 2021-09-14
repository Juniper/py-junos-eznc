from select import select
import re
import datetime
from jnpr.junos.utils.ssh_client import open_ssh_client

_JUNOS_PROMPT = "> "
_SHELL_PROMPT = "(%|#|\$)\s"
_SELECT_WAIT = 0.1
_RECVSZ = 1024


class StartShell(object):

    """
    Junos shell execution utility.  This utility is written to
    support the "context manager" design pattern.  For example::

        def _ssh_exec(self, command):
            with StartShell(self._dev) as sh:
                got = sh.run(command)
            return got

    """

    def __init__(self, nc, timeout=30):
        """
        Utility Constructor

        :param Device nc: The Device object

        :param int timeout:
          Timeout value in seconds to wait for expected string/pattern.
        """
        self._nc = nc
        self.timeout = timeout
        self._client = None
        self._chan = None

    def wait_for(self, this=_SHELL_PROMPT, timeout=0):
        """
        Wait for the result of the command, expecting **this** prompt.

        :param str this: expected string/pattern.

        :param int timeout:
          Timeout value in seconds to wait for expected string/pattern.
          If not specified defaults to self.timeout.

        :returns: resulting string of data in a list
        :rtype: list

        .. warning:: need to add a timeout safeguard
        """
        chan = self._chan
        got = []
        timeout = timeout or self.timeout
        timeout = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
        while timeout > datetime.datetime.now():
            rd, wr, err = select([chan], [], [], _SELECT_WAIT)
            if rd:
                data = chan.recv(_RECVSZ)
                if isinstance(data, bytes):
                    data = data.decode("utf-8", "replace")
                got.append(data)
                if this is not None and re.search(r"{}\s?$".format(this), data):
                    break
        return got

    def send(self, data):
        """
        Send the command **data** followed by a newline character.

        :param str data: the data to write out onto the shell.
        :returns: result of SSH channel send
        """
        self._chan.send(data)
        self._chan.send("\n")

    def open(self):
        """
        Open an ssh-client connection and issue the 'start shell' command to
        drop into the Junos shell (csh).  This process opens a
        :class:`paramiko.SSHClient` instance.
        """
        self._client = open_ssh_client(dev=self._nc)
        self._chan = self._client.invoke_shell()

        got = self.wait_for(r"(%|>|#|\$)")
        if got[-1].endswith(_JUNOS_PROMPT):
            self.send("start shell")
            self.wait_for(_SHELL_PROMPT)

    def close(self):
        """Close the SSH client channel"""
        self._chan.close()
        self._client.close()

    def run(self, command, this=_SHELL_PROMPT, timeout=0):
        """
        Run a shell command and wait for the response.  The return is a
        tuple. The first item is True/False if exit-code is 0.  The second
        item is the output of the command.

        :param str command: the shell command to execute
        :param str this: the expected shell-prompt to wait for. If ``this`` is
          set to None, function will wait for all the output on the shell till
          timeout value.
        :param int timeout:
          Timeout value in seconds to wait for expected string/pattern (this).
          If not specified defaults to self.timeout. This timeout is specific
          to individual run call. If ``this`` is provided with None value,
          function will wait till timeout value to grab all the content from
          command output.

        :returns: (last_ok, result of the executed shell command (str) )

        .. code-block:: python

           with StartShell(dev) as ss:
               print ss.run('cprod -A fpc0 -c "show version"', timeout=10)

        .. note:: as a *side-effect* this method will set the ``self.last_ok``
                  property.  This property is set to ``True`` if ``$?`` is
                  "0"; indicating the last shell command was successful else
                  False. If ``this`` is set to None, last_ok will be set to
                  True if there is any content in result of the executed shell
                  command.
        """
        timeout = timeout or self.timeout
        # run the command and capture the output
        self.send(command)
        got = "".join(self.wait_for(this, timeout))
        self.last_ok = False
        if this is None:
            self.last_ok = got is not ""
        elif this != _SHELL_PROMPT:
            self.last_ok = re.search(r"{}\s?$".format(this), got) is not None
        elif re.search(r"{}\s?$".format(_SHELL_PROMPT), got) is not None:
            # use $? to get the exit code of the command
            self.send("echo $?")
            rc = "".join(self.wait_for(_SHELL_PROMPT))
            self.last_ok = rc.find("\r\n0\r\n") > 0
        return (self.last_ok, got)

    # -------------------------------------------------------------------------
    # CONTEXT MANAGER
    # -------------------------------------------------------------------------

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_ty, exc_val, exc_tb):
        self.close()
