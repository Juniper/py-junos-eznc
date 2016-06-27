import unittest2 as unittest
from jnpr.junos.utils.config import Config
from nose.plugins.attrib import attr
from mock import MagicMock, patch
import re
import sys
import os
from lxml import etree

from jnpr.junos.console import Console
from jnpr.junos.transport.tty_netconf import tty_netconf


if sys.version<'3':
    builtin_string = '__builtin__'
else:
    builtin_string = 'builtins'

@attr('unit')
class TestConsole(unittest.TestCase):

    @patch('jnpr.junos.transport.tty_telnet.Telnet._tty_open')
    @patch('jnpr.junos.transport.tty_telnet.telnetlib.Telnet.expect')
    @patch('jnpr.junos.transport.tty_telnet.Telnet.write')
    def setUp(self, mock_write, mock_expect, mock_open):
        tty_netconf.open = MagicMock()
        mock_expect.side_effect=[(1, re.search('(?P<login>ogin:\s*$)', "login: "), '\r\r\n ogin:'),
                                (2, re.search('(?P<passwd>assword:\s*$)', "password: "), '\r\r\n password:'),
                                (3, re.search('(?P<shell>%|#\s*$)', "junos % "), '\r\r\nroot@device:~ # ')]
        self.dev = Console(host='1.1.1.1', user='lab', password='lab123', mode = 'Telnet')
        self.dev.open()

    @patch('jnpr.junos.transport.tty.tty_netconf.close')
    @patch('jnpr.junos.transport.tty_telnet.telnetlib.Telnet.expect')
    @patch('jnpr.junos.transport.tty_telnet.Telnet.write')
    def tearDown(self, mock_write, mock_expect, mock_nc_close):
        mock_expect.side_effect = [(1, re.search('(?P<cli>[^\\-"]>\s*$)', "cli>"), '\r\r\nroot@device>'),
                                   (2, re.search('(?P<shell>%|#\s*$)', "junos %"), '\r\r\nroot@device:~ # '),
                                   (3, re.search('(?P<login>ogin:\s*$)', "login: "), '\r\r\nlogin')]
        self.dev.close()

    @patch('jnpr.junos.console.Console._tty_logout')
    def tearDown(self, mock_tty_logout):
        self.dev.close()

    @patch('jnpr.junos.console.Console._tty_login')
    def test_console_open_error(self, mock_tty_login):
        mock_tty_login.side_effect = RuntimeError
        self.assertRaises(RuntimeError, self.dev.open)

    def test_console_connected(self):
        self.assertTrue(self.dev.connected)
        self.assertFalse(self.dev.gather_facts)

    @patch('jnpr.junos.console.Console._tty_logout')
    def test_console_close_error(self, mock_logout):
        mock_logout.side_effect = RuntimeError
        self.assertRaises(RuntimeError, self.dev.close)

    # @patch('jnpr.junos.transport.tty_telnet.Telnet._tty_close')
    # def test_console_close_error2(self, mock_close):
    #     mock_close.side_effect = RuntimeError
    #     self.assertRaises(RuntimeError, self.dev.close(True))

    @patch('jnpr.junos.transport.tty_netconf.tty_netconf.rpc')
    def test_console_zeroize(self, mock_zeroize):
        self.dev.zeroize()
        self.assertTrue(mock_zeroize.called)

    @patch('jnpr.junos.transport.tty_netconf.tty_netconf.rpc')
    @patch('jnpr.junos.console.FACT_LIST')
    def test_console_gather_facts(self, mock_fact_list, mock_rpc):
        from jnpr.junos.facts.session import facts_session
        mock_fact_list.__iter__.return_value = [facts_session]
        self.dev._gather_facts()
        self.assertEqual(mock_rpc.call_count, 1)

    @patch('jnpr.junos.transport.tty_telnet.telnetlib.Telnet.write')
    @patch('jnpr.junos.transport.tty_netconf.select.select')
    @patch('jnpr.junos.transport.tty_telnet.telnetlib.Telnet.read_until')
    def test_load_console(self, mock_read_until, mock_select, mock_write):
        mock_select.return_value = ([self.dev._tty._rx], [], [])
        xml = """<policy-options>
                  <policy-statement>
                    <name>F5-in</name>
                    <term>
                        <name>testing</name>
                        <then>
                            <accept/>
                        </then>
                    </term>
                    <from>
                        <protocol>mpls</protocol>
                    </from>
                </policy-statement>
                </policy-options>"""

        mock_read_until.return_value = """
        <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:junos="http://xml.juniper.net/junos/15.2I0/junos">
            <load-configuration-results>
            <ok/>
            </load-configuration-results>
            </rpc-reply>
            ]]>]]>"""
        cu = Config(self.dev)
        cu.load(xml, format='xml')
        cu.commit()


    @patch('jnpr.junos.transport.tty_netconf.tty_netconf._receive')
    @patch('jnpr.junos.transport.tty_telnet.Telnet.rawwrite')
    def test_console_rpc_call(self, mock_write, mock_rcv):
        mock_rcv.side_effect = self._mock_manager
        self.dev.rpc.get_chassis_inventory()
        self.assertTrue(mock_rcv.called)

    @patch('jnpr.junos.transport.tty_netconf.remove_namespaces')
    @patch('jnpr.junos.transport.tty_netconf.tty_netconf._receive')
    @patch('jnpr.junos.transport.tty_telnet.Telnet.rawwrite')
    def test_console_rpc_call_exception(self, mock_write, mock_rcv, mock_ns):
        mock_rcv.return_value = etree.fromstring('<output>testing</output>')
        mock_ns.side_effect = IndexError('testing')
        op = self.dev.rpc.get_chassis_inventory()
        self.assertEqual(op.tag, 'output')

    # below 2 function will be used in future.
    def _mock_manager(self, *args, **kwargs):
        if args:
            return self._read_file(args[0].tag + '.xml')

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        with open(fpath) as fp:
            foo = fp.read()
        if fname == 'get-system-users-information.xml':
            return NCElement(foo,
                             self.dev._conn._device_handler.transform_reply())
        rpc_reply = NCElement(foo, self.dev._conn.
                              _device_handler.transform_reply()) \
            ._NCElement__doc[0]
        return rpc_reply