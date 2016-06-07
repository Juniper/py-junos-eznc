import unittest2 as unittest
from nose.plugins.attrib import attr
from mock import MagicMock, patch
import re
import sys

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
        mock_expect.side_effect=[(1, re.search('(?P<login>ogin:\s*$)', "login: "), '\r\r\nbng-ui-vm-92 login:'),
                                (2, re.search('(?P<passwd>assword:\s*$)', "password: "), '\r\r\nbng-ui-vm-92 passd:'),
                                 (3, re.search('(?P<shell>%|#\s*$)', "junos % "), '\r\r\nbng-ui-vm-92 junos %')]


        self.dev = Console(host='1.1.1.1', user='lab', password='lab123', mode = 'Telnet')
        self.dev.open()

    @patch('jnpr.junos.console.Console._tty_logout')
    def tearDown(self, mock_tty_logout):
        self.dev.close()

    def test_console_connected(self):
        self.assertTrue(self.dev.connected)
        self.assertFalse(self.dev.gather_facts)
