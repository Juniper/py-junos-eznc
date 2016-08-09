import unittest2 as unittest
from nose.plugins.attrib import attr
from mock import MagicMock, patch
import sys

from jnpr.junos.console import Console

if sys.version < '3':
    builtin_string = '__builtin__'
else:
    builtin_string = 'builtins'


@attr('unit')
class TestSerial(unittest.TestCase):

    @patch('jnpr.junos.transport.tty_serial.serial.Serial.open')
    @patch('jnpr.junos.transport.tty_serial.serial.Serial.write')
    @patch('jnpr.junos.transport.tty_serial.serial.Serial.flush')
    @patch('jnpr.junos.transport.tty_serial.Serial.read_prompt')
    @patch('jnpr.junos.transport.tty.tty_netconf.open')
    def setUp(self, mock_nc_open, mock_read,
              mock_flush, mock_write, mock_open):
        self.dev = Console(port='USB/ttyUSB0', baud=9600, mode='Serial')
        mock_read.side_effect = [
            ('login', 'login'), ('passwd', 'passwd'), ('shell', 'shell')]
        self.dev.open()

    @patch('jnpr.junos.transport.tty.tty_netconf.close')
    @patch('jnpr.junos.transport.tty_serial.Serial.read_prompt')
    @patch('jnpr.junos.transport.tty_serial.Serial.write')
    @patch('jnpr.junos.transport.tty_serial.Serial._tty_close')
    def tearDown(self, mock_serial_close, mock_write, mock_read, mock_close):
        mock_read.side_effect = [
            ('cli', 'cli'), ('shell', 'shell'), ('login', 'login')]
        self.dev.close()

    def test_console_connected(self):
        self.assertTrue(self.dev.connected)

    def test_close_connection(self):
        self.dev._tty._ser = MagicMock()
        self.dev.close(skip_logout=True)
        self.assertTrue(self.dev._tty._ser.close.called)
