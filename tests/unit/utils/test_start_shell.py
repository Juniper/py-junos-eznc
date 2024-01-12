import unittest
import nose2

from jnpr.junos import Device
from jnpr.junos.utils.start_shell import StartShell

from mock import patch, MagicMock, call

__author__ = "Rick Sherman"
__credits__ = "Jeremy Schulman, Nitin Kumar"


class TestStartShell(unittest.TestCase):
    @patch("paramiko.SSHClient")
    def setUp(self, mock_connect):
        self.dev = Device(host="1.1.1.1")
        self.shell = StartShell(self.dev)

    @patch("paramiko.SSHClient")
    @patch("jnpr.junos.utils.start_shell.StartShell.wait_for")
    def test_startshell_open_with_shell_term(self, mock_wait, mock_connect):
        mock_wait.return_value = ["user # "]
        self.shell.open()
        mock_wait.assert_called_with("(%|>|#|\\$)")

    @patch("paramiko.SSHClient")
    @patch("jnpr.junos.utils.start_shell.StartShell.wait_for")
    def test_startshell_open_with_junos_term(self, mock_wait, mock_connect):
        mock_wait.return_value = ["user > "]
        self.shell.open()
        mock_wait.assert_called_with("(%|#|\\$)\\s")

    @patch("paramiko.SSHClient")
    @patch("jnpr.junos.utils.start_shell.StartShell.wait_for")
    def test_startshell_open_with_bourne_shell(self, mock_wait, mock_connect):
        mock_wait.return_value = ["foo@bar:~$ "]
        self.shell.open()
        mock_wait.assert_called_with("(%|>|#|\\$)")

    @patch("paramiko.SSHClient")
    def test_startshell_close(self, mock_connect):
        self.shell._chan = MagicMock()
        self.shell._client = MagicMock()
        self.shell.close()
        self.shell._client.close.assert_called_once()

    @patch("jnpr.junos.utils.start_shell.StartShell.wait_for")
    def test_startshell_run(self, mock_wait):
        self.shell._chan = MagicMock()
        mock_wait.return_value = ["user % "]
        self.shell.run("ls")
        self.assertTrue(call.send("echo $?") in self.shell._chan.mock_calls)

    @patch("jnpr.junos.utils.start_shell.select")
    def test_startshell_wait_for(self, mock_select):
        mock_select.return_value = ["> ", 2, 3]
        self.shell._chan = MagicMock()
        self.shell._chan.recv.return_value = "> "
        self.assertTrue(self.shell.wait_for("> ")[0].endswith("> "))

    @patch("jnpr.junos.utils.start_shell.select")
    def test_startshell_wait_for_regex(self, mock_select):
        mock_select.return_value = ["> ", 2, 3]
        self.shell._chan = MagicMock()
        # output from command: cli -c "show version"
        self.shell._chan.recv.return_value = """
        ------------
        JUNOS Services Deep Packet Inspection package [15.1
        ---(more)---
        """
        self.assertTrue(
            str(self.shell.wait_for("---\(more\s?\d*%?\)---\n\s*|%")[0])
            in self.shell._chan.recv.return_value
        )

    @patch("jnpr.junos.utils.start_shell.StartShell.open")
    @patch("jnpr.junos.utils.start_shell.StartShell.close")
    def test_startshell_context(self, mock_close, mock_open):
        with StartShell(self.dev) as shell:
            shell._chan = MagicMock()
            shell.send("test")
        mock_close.assert_called_once_with()

    @patch("jnpr.junos.utils.start_shell.StartShell.wait_for")
    def test_startshell_run_regex(self, mock_wait_for):
        self.shell._chan = MagicMock()
        mock_wait_for.return_value = [
            """
        ------------
        JUNOS Services Deep Packet Inspection package [15.1
        ---(more)---
        """
        ]
        self.assertTrue(
            self.shell.run("show version", "---\(more\s?\d*%?\)---\n\s*|%")[0]
        )

    @patch("jnpr.junos.utils.start_shell.StartShell.wait_for")
    def test_startshell_run_this_None(self, mock_wait_for):
        self.shell._chan = MagicMock()
        mock_wait_for.return_value = [
            """
        ------------
        JUNOS Services Deep Packet Inspection package [15.1
        """
        ]
        self.assertTrue(self.shell.run("show version", this=None)[0])
