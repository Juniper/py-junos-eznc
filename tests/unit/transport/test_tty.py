import logging

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import nose2
from mock import MagicMock, patch

from jnpr.junos.transport.tty import Terminal
from jnpr.junos import exception as EzErrors


class TestTTY(unittest.TestCase):
    def setUp(self):
        logging.getLogger("jnpr.junos.tty")
        self.terminal = Terminal(user="test", password="password123", attempts=1)

    def test_login_bad_password_runtimeerror(self):
        self.terminal._badpasswd = 4
        self.terminal.read_prompt = MagicMock()
        self.terminal.read_prompt.return_value = (None, "badpasswd")
        self.terminal.write = MagicMock()
        self.assertRaises(RuntimeError, self.terminal._login_state_machine)

    def test_login_bad_password_ConnectAuthError(self):
        self.terminal._badpasswd = 1
        self.terminal.read_prompt = MagicMock()
        self.terminal.read_prompt.return_value = (None, "badpasswd")
        self.terminal.write = MagicMock()
        self.assertRaises(EzErrors.ConnectAuthError, self.terminal._login_state_machine)

    @patch("jnpr.junos.transport.tty.sleep")
    def test_tty_no_login(self, mock_sleep):
        self.terminal._badpasswd = 4
        self.terminal.read_prompt = MagicMock()
        self.terminal.read_prompt.return_value = (None, "testing")
        self.terminal.write = MagicMock()
        self.assertRaises(RuntimeError, self.terminal._login_state_machine)
        self.terminal.write.assert_called_with("\n")
        self.terminal.read_prompt.return_value = (None, "testing")
        self.terminal.write = MagicMock()
        self.assertRaises(RuntimeError, self.terminal._login_state_machine)
        self.terminal.write.assert_called_with("<close-session/>")

    @patch("jnpr.junos.transport.tty.sleep")
    @patch("jnpr.junos.transport.tty.logger")
    def test_tty_cli(self, mock_logger, mock_sleep):
        self.terminal.read_prompt = MagicMock()
        self.terminal.read_prompt.return_value = (None, "cli")
        self.terminal._login_state_machine()
        self.assertEqual(self.terminal.state, 4)

    @patch("jnpr.junos.transport.tty.sleep")
    def test_loader(self, mock_sleep):
        self.terminal.write = MagicMock()
        self.terminal.read_prompt = MagicMock()
        self.terminal._loader = 2
        # self.terminal._login_state_machine = MagicMock()
        self.terminal.read_prompt.side_effect = [(None, "loader"), (None, "testing")]
        self.assertRaises(RuntimeError, self.terminal._login_state_machine)
        mock_sleep.assert_called_with(300)

    @patch("jnpr.junos.transport.tty.logger")
    def test_ev_shell(self, mock_logger):
        self.terminal.write = MagicMock()
        self.terminal.read_prompt = MagicMock()
        self.terminal.read_prompt.return_value = (None, "shell")
        self.terminal._login_state_machine()
        self.assertEqual(self.terminal.state, 4)

    @patch("jnpr.junos.transport.tty.sleep")
    def test_ev_option(self, mock_sleep):
        self.terminal.write = MagicMock()
        self.terminal.read_prompt = MagicMock()
        self.terminal.read_prompt.return_value = (None, "option")
        self.assertRaises(RuntimeError, self.terminal._login_state_machine)
        self.terminal.write.assert_called_with("1")
        self.assertEqual(self.terminal.state, 7)

    @patch("jnpr.junos.transport.tty.sleep")
    def test_tty_ev_netconf_closed(self, mock_sleep):
        self.terminal.write = MagicMock()
        self.terminal._tty_close = MagicMock()
        self.terminal.read_prompt = MagicMock()
        self.terminal.read_prompt.side_effect = iter(
            [(None, "netconf_closed"), (None, "shell"), (None, "login")]
        )
        self.assertTrue(self.terminal._logout_state_machine())

    @patch("jnpr.junos.transport.tty.sleep")
    def test_tty_already_logout(self, mock_sleep):
        self.terminal.write = MagicMock()
        self.terminal.read_prompt = MagicMock()
        self.terminal.read_prompt.return_value = (None, None)
        self.assertTrue(self.terminal._logout_state_machine())

    @patch("jnpr.junos.transport.tty.sleep")
    def test_tty_login_state_machine_loader(self, mock_sleep):
        self.terminal.write = MagicMock()
        self.terminal._loader = 1
        self.terminal.read_prompt = MagicMock()
        self.terminal.read_prompt.side_effect = iter(
            [(None, "loader"), (None, "hotkey"), (None, "shell")]
        )
        self.assertRaises(RuntimeError, self.terminal._login_state_machine)

    @patch("jnpr.junos.transport.tty.sleep")
    def test_tty_login_state_machine_loader(self, mock_sleep):
        self.terminal.write = MagicMock()
        self.terminal._loader = 1
        self.terminal.read_prompt = MagicMock()
        self.terminal.read_prompt.side_effect = iter(
            [(None, "loader"), (None, "shell")]
        )
        try:
            self.terminal._login_state_machine()
        except RuntimeError as ex:
            self.assertEqual(str(ex), "probably corrupted image, stuck in loader")

    @patch("jnpr.junos.transport.tty.sleep")
    def test_tty_login_state_machine_hotkey(self, mock_sleep):
        self.terminal.write = MagicMock()
        self.terminal.read_prompt = MagicMock()
        self.terminal.read_prompt.return_value = (None, "hotkey")
        self.assertRaises(RuntimeError, self.terminal._login_state_machine)
        self.assertEqual(self.terminal.state, 8)  # 8 is for hot keys

    @patch("jnpr.junos.transport.tty.sleep")
    def test_tty_ev_tty_nologin(self, mock_sleep):
        self.terminal.write = MagicMock()
        self.terminal.read_prompt = MagicMock()
        self.terminal.read_prompt.return_value = (None, None)
        self.terminal.console_has_banner = True
        self.assertRaises(RuntimeError, self.terminal._login_state_machine)
        self.terminal.write.assert_called_with("\n")

    @patch("jnpr.junos.transport.tty.sleep")
    def test_tty_logout_state_machine_attempt_10(self, mock_sleep):
        self.terminal.write = MagicMock()
        self.terminal.read_prompt = MagicMock()
        self.terminal.read_prompt.return_value = (None, "cli")
        try:
            self.terminal._logout_state_machine()
        except RuntimeError as ex:
            self.assertEqual(str(ex), "logout_sm_failure")
