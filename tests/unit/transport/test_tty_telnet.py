import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import nose2
from mock import MagicMock, patch
from jnpr.junos.transport.tty_telnet import Telnet
import six


class TestTTYTelnet(unittest.TestCase):
    @patch("jnpr.junos.transport.tty_telnet.telnetlib.Telnet")
    def setUp(self, mpock_telnet):
        self.tel_conn = Telnet(
            host="1.1.1.1", user="test", password="password123", port=23, timeout=30
        )

    def test_open(self):
        self.tel_conn._tty_open()
        self.tel_conn._tn.open.assert_called()

    def test_open_exception(self):
        self.tel_conn._tn.open.side_effect = Exception
        Telnet.RETRY_OPEN = 1
        Telnet.RETRY_BACKOFF = 0.1
        self.assertRaises(RuntimeError, self.tel_conn._tty_open)
        # reset
        Telnet.RETRY_OPEN = 3
        Telnet.RETRY_BACKOFF = 2

    def test_close(self):
        self.tel_conn._tty_close()
        self.tel_conn._tn.close.assert_called()

    def test_read(self):
        self.tel_conn.read()
        self.tel_conn._tn.read_until.assert_called()

    @patch("jnpr.junos.transport.tty_telnet.telnetlib.Telnet")
    def test_tty_telnet_baud(self, mock_telnet):
        tel_conn = Telnet(
            host="1.1.1.1",
            user="test",
            password="password123",
            port=23,
            timeout=30,
            baud=0,
        )
        tel_conn._tty_open()
        tel_conn.rawwrite("<rpc>")
        tel_conn._tn.write.assert_called_with("<rpc>")

    def test_read_prompt_RuntimeError(self):
        self.tel_conn.expect = MagicMock()
        self.tel_conn.expect = (None, None, "port already in use")
        self.assertRaises(RuntimeError, self.tel_conn._login_state_machine)

    def test_read_prompt_in_use_RuntimeError(self):
        self.tel_conn.expect = MagicMock()
        self.tel_conn._tn.expect.return_value = (
            None,
            None,
            six.b("port already in use"),
        )
        self.assertRaises(RuntimeError, self.tel_conn._login_state_machine)

    def test_tty_telnet_rawwrite_sys_py3(self):
        with patch.object(sys.modules["sys"], "version", "3.x") as mock_sys:
            self.tel_conn._tty_open()
            content = MagicMock()
            self.tel_conn.rawwrite(content)
            content.decode.assert_called_with("utf-8")
