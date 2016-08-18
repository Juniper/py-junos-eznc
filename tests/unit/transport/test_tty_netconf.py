import unittest2 as unittest
from nose.plugins.attrib import attr
from mock import MagicMock, patch
from jnpr.junos.transport.tty_netconf import tty_netconf
import six


@attr('unit')
class TestTTYNetconf(unittest.TestCase):

    def setUp(self):
        self.tty_net = tty_netconf(MagicMock())

    @patch('jnpr.junos.transport.tty_netconf.tty_netconf._receive')
    def test_open_at_shell_true(self, mock_rcv):
        mock_rcv.return_value = ']]>]]>'
        self.tty_net.open(True)
        self.tty_net._tty.write.assert_called_with(
            'xml-mode netconf need-trailer')

    @patch('jnpr.junos.transport.tty_netconf.tty_netconf._receive')
    @patch('jnpr.junos.transport.tty_netconf.timedelta')
    def test_open_RuntimeError(self, mock_delta, mock_rcv):
        mock_rcv.return_value = ']]>]]>'
        self.tty_net._tty.read.return_value = six.b('testing')
        from datetime import timedelta
        mock_delta.return_value = timedelta(seconds=0.5)
        self.assertRaises(RuntimeError, self.tty_net.open, False)
        self.tty_net._tty.write.assert_called_with(
            'junoscript netconf need-trailer')

    @patch('jnpr.junos.transport.tty_netconf.tty_netconf._receive')
    def test_rpc(self, mock_rcv):
        mock_rcv.return_value = ']]>]]>'
        self.tty_net.rpc('get-interface-information')
        self.tty_net._tty.rawwrite.assert_called_with(
            six.b('<rpc><get-interface-information/></rpc>'))

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
        mock_rpc.side_effect = ValueError
        self.assertTrue(not self.tty_net.zeroize())
