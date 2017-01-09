import unittest2 as unittest
from nose.plugins.attrib import attr
from mock import MagicMock, patch
from jnpr.junos.transport.tty_netconf import tty_netconf
import six
import os
import select
import socket
from ncclient.operations import RPCError


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

    @patch('ncclient.operations.rpc.RPCReply.parse')
    @patch('jnpr.junos.transport.tty_netconf.tty_netconf._receive')
    def test_rpc(self, mock_rcv, mock_parse):
        mock_rcv.return_value = ']]>]]>'
        self.tty_net.rpc('get-interface-information')
        self.tty_net._tty.rawwrite.assert_called_with(
            six.b('<rpc><get-interface-information/></rpc>'))

    @patch('jnpr.junos.transport.tty_netconf.tty_netconf._receive')
    def test_tty_netconf_single_rpc_error(self, mock_rcv):
        mock_rcv.return_value = """
        <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <rpc-error><error-type>protocol</error-type>
        <error-tag>operation-failed</error-tag>
        <error-severity>error</error-severity>
        <error-message>interface-ranges expansion failed
        </error-message></rpc-error></rpc-reply>"""
        self.assertRaises(RPCError, self.tty_net.rpc, 'commit-configuration')

    @patch('jnpr.junos.transport.tty_netconf.tty_netconf._receive')
    def test_tty_netconf_multi_rpc_error(self, mock_rcv):
        mock_rcv.return_value = self._read_file('commit-configuration.xml')
        self.assertRaises(RPCError, self.tty_net.rpc, 'commit-configuration')

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

    @patch('jnpr.junos.transport.tty_netconf.select.select')
    def test_tty_netconf_receive_select_error(self, mock_select):
        mock_select.side_effect = select.error
        self.assertRaises(select.error, self.tty_net._receive)

    @patch('jnpr.junos.transport.tty_netconf.select.select')
    def test_tty_netconf_receive_socket_error(self, mock_select):
        mock_select.side_effect = socket.error
        self.assertRaises(socket.error, self.tty_net._receive)

    @patch('jnpr.junos.transport.tty_netconf.select.select')
    def test_tty_netconf_receive_empty_line(self, mock_select):
        rx = MagicMock()
        rx.read_until.side_effect = iter([
            six.b(''), six.b(']]>]]>')])
        mock_select.return_value = ([rx], [], [])
        self.assertEqual(self.tty_net._receive().tag, 'error-in-receive')

    @patch('jnpr.junos.transport.tty_netconf.select.select')
    def test_tty_netconf_receive_splited_eom(self, mock_select):
        rx = MagicMock()
        rx.read_until.side_effect = iter(['testing]', ']>', ']]>'])
        mock_select.return_value = ([rx], [], [])
        self.assertEqual(self.tty_net._receive().tag, 'error-in-receive')

    @patch('jnpr.junos.transport.tty_netconf.select.select')
    def test_tty_netconf_receive_splited_eom(self, mock_select):
        rx = MagicMock()
        rx.read_until.side_effect = iter([six.b(i) for i in
                                          ['testing]', ']>', ']]>']])
        mock_select.return_value = ([rx], [], [])
        self.assertEqual(self.tty_net._receive().tag, 'error-in-receive')

    @patch('jnpr.junos.transport.tty_netconf.select.select')
    def test_tty_netconf_receive_XMLSyntaxError(self, mock_select):
        rx = MagicMock()
        rx.read_until.side_effect = iter([
            six.b('<rpc-reply>ok<dummy></rpc-reply>'),
            six.b('\n]]>]]>')])
        mock_select.return_value = ([rx], [], [])
        self.assertEqual(self.tty_net._receive(),
                         six.b('<rpc-reply>ok<dummy/></rpc-reply>'))

    @patch('jnpr.junos.transport.tty_netconf.select.select')
    def test_tty_netconf_receive_XMLSyntaxError_eom_in_center(
            self, mock_select):
        rx = MagicMock()
        rx.read_until.side_effect = iter([
            six.b('<rpc-reply>ok</rpc-reply>'),
            six.b(']]>]]>\ndummy')])
        mock_select.return_value = ([rx], [], [])
        self.assertEqual(self.tty_net._receive(),
                         six.b('<rpc-reply>ok</rpc-reply>'))

    @patch('jnpr.junos.transport.tty_netconf.select.select')
    def test_tty_netconf_receive_xmn_error(
            self, mock_select):
        rx = MagicMock()
        rx.read_until.side_effect = iter([
            six.b('<message>ok</message>'),
            six.b('\n</xnm:error>\n'),
            six.b(']]>]]>\ndummy')])
        mock_select.return_value = ([rx], [], [])
        self.assertEqual(self.tty_net._receive().tag,
                         'error-in-receive')

    def _read_file(self, fname):
        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()

        # specific to multi rpc error
        if fname == 'commit-configuration.xml':
            return foo
