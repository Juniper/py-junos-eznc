import paramiko
from select import select

_JUNOS_PROMPT = '> '
_SHELL_PROMPT = '% '
_SELECT_WAIT = 0.1
_RECVSZ = 1024


class StartShell(object):

    def __init__(self, nc):
        self._nc = nc

    def wait_for(self, this=_SHELL_PROMPT):
        """
        wait for the result of the command, expecting :this:
        @@@ need to add a timeout safeguard
        """
        chan = self._chan
        got = []
        while True:
            rd, wr, err = select([chan], [], [], _SELECT_WAIT)
            if rd:
                data = chan.recv(_RECVSZ)
                got.append(data)
                if data.endswith(this):
                    break
        return got

    def send(self, data):
        """
        send the command :data: followed by a \'\\\\n\' character
        """
        self._chan.send(data)
        self._chan.send('\n')

    def open(self):
        """
        open an ssh-client connection and issue the 'start shell' command to
        drop into the Junos shell (csh).
        """
        junos = self._nc

        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=junos.hostname,
                       port=(22, junos._port)[junos.hostname == 'localhost'],
                       username=junos._auth_user,
                       password=junos._auth_password,
                       )

        chan = client.invoke_shell()
        self._client = client
        self._chan = chan

        self.wait_for(_JUNOS_PROMPT)
        self.send('start shell')
        self.wait_for(_SHELL_PROMPT)

    def close(self):
        self._chan.close()
        self._client.close()

    def run(self, command, this=_SHELL_PROMPT):
        """
        run a shell command and wait for the response.  The return is a
        tuple. The first item is True/False if exit-code is 0.  The second
        item is the output of the command.
        """
        # run the command and capture the output
        self.send(command)
        got = self.wait_for(this)

        # use $? to get the exit code of the command
        self.send('echo $?')
        rc = ''.join(self.wait_for(this))
        self.last_ok = True if rc.find('0') > 0 else False

        return got

    # -------------------------------------------------------------------------
    # CONTEXT MANAGER
    # -------------------------------------------------------------------------

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_ty, exc_val, exc_tb):
        self.close()
