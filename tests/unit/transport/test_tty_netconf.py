import unittest2 as unittest
from nose.plugins.attrib import attr
from mock import MagicMock, patch
from jnpr.junos.transport.tty_netconf import tty_netconf


@attr('unit')
class TestTTYNetconf(unittest.TestCase):

    def setUp(self):
        self.tty_net = tty_netconf(MagicMock())

    @patch('jnpr.junos.transport.tty_netconf.tty_netconf._receive')
    def test_open_at_shell_true(self, mock_rcv):
        mock_rcv.return_value=']]>]]>'
        self.tty_net.open(True)
        self.tty_net._tty.write.assert_called_with('xml-mode netconf need-trailer')

    @patch('jnpr.junos.transport.tty_netconf.tty_netconf.rpc')
    def test_close_force_true(self, mock_rpc):
        self.tty_net.close(True)
        mock_rpc.assert_called_with('close-session')


    @patch('jnpr.junos.transport.tty_netconf.tty_netconf.rpc')
    def test_close_force_false(self, mock_rpc):
        self.tty_net.close(False)
        mock_rpc.assert_not_called_with('close-session')

    @patch('jnpr.junos.transport.tty_netconf.tty_netconf.rpc')
    def test_zeroize_exception(self, mock_rpc):
        mock_rpc.side_effect=ValueError
        self.assertTrue(not self.tty_net.zeroize())