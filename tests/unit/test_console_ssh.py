import unittest2 as unittest
from nose.plugins.attrib import attr
from mock import MagicMock, patch
import re
import sys

from jnpr.junos.console import Console
from jnpr.junos.transport.tty_netconf import tty_netconf
from jnpr.junos.transport.tty_ssh import SecureShell

if sys.version<'3':
    builtin_string = '__builtin__'
else:
    builtin_string = 'builtins'

@attr('unit')
class TestSecureShell(unittest.TestCase):

    @patch('jnpr.junos.transport.tty_ssh.SecureShell._tty_open')
    @patch('jnpr.junos.transport.paramiko.SSHClient.connect')
    @patch('jnpr.junos.transport.tty_telnet.Telnet.write')
    def setUp(self, mock_connect, mock_open):
        tty_netconf.open = MagicMock()
        self.dev = Console(host='1.1.1.1', user='lab', password='lab123', mode = 'ssh')
        self.dev.open()

    @patch('jnpr.junos.console.Console._tty_logout')
    def tearDown(self, mock_tty_logout):
        self.dev.close()

    @patch('jnpr.junos.transport.tty_ssh.SecureShell._tty_open')
    def test_ssh_open(self, mock_open):
        self.assertEqual(mock_open.call_count, 1)
        self.assertTrue(self.dev.connected)
        self.assertFalse(self.dev.gather_facts)

