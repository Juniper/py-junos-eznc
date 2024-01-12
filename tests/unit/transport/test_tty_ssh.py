import socket
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import nose2
from mock import MagicMock, patch
from jnpr.junos.transport.tty_ssh import SSH


class TestTTYSSH(unittest.TestCase):
    @patch("jnpr.junos.transport.tty_ssh.paramiko")
    def setUp(self, mock_paramiko):
        self.ssh_conn = SSH(
            host="1.1.1.1", user="test", password="password123", port=3007, timeout=30
        )
        self._ssh = mock_paramiko.invoke_shell

    def test_open(self):
        self.ssh_conn._tty_open()
        self.ssh_conn._ssh_pre.connect.assert_called()

    def test_open_exception(self):
        self.ssh_conn._ssh_pre.connect.side_effect = socket.error
        SSH.RETRY_OPEN = 1
        SSH.RETRY_BACKOFF = 0.1
        self.assertRaises(RuntimeError, self.ssh_conn._tty_open)
        # reset
        SSH.RETRY_OPEN = 3
        SSH.RETRY_BACKOFF = 2

    def test_read(self):
        self.ssh_conn._tty_open()
        self.assertRaises(ValueError, self.ssh_conn.read)

    def test_close(self):
        self.assertEqual(self.ssh_conn._tty_close(), None)

    @patch("jnpr.junos.transport.tty_ssh.paramiko")
    def test_tty_ssh_baud(self, mock_paramiko):
        self.ssh_conn = SSH(
            host="1.1.1.1",
            user="test",
            password="password123",
            port=3007,
            timeout=30,
            baud=0,
        )

        self.ssh_conn._tty_open()
        self.ssh_conn.rawwrite("<rpc>")
        self.ssh_conn._ssh.sendall.assert_called_with("<rpc>")

    def test_tty_ssh_rawwrite_sys_py3(self):
        with patch.object(sys.modules["sys"], "version", "3.x") as mock_sys:
            self.ssh_conn._tty_open()
            content = MagicMock()
            self.ssh_conn.rawwrite(content)
            content.decode.assert_called_with("utf-8")
