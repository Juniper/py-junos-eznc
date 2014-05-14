__author__ = "Rick Sherman"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import unittest
from nose.plugins.attrib import attr

from jnpr.junos import Device
from jnpr.junos.utils.start_shell import StartShell

from mock import patch, MagicMock, call


@attr('unit')
class TestStartShell(unittest.TestCase):
    @patch('paramiko.SSHClient')
    def setUp(self, mock_connect):
        self.dev = Device(host='1.1.1.1')
        self.shell = StartShell(self.dev)

    @patch('paramiko.SSHClient')
    @patch('jnpr.junos.utils.start_shell.StartShell.wait_for')
    def test_startshell_open(self, mock_connect, mock_wait):
        self.shell.open()
        mock_connect.assert_called_with('% ')

    @patch('paramiko.SSHClient')
    def test_startshell_close(self, mock_connect):
        self.shell._chan = MagicMock()
        self.shell._client = MagicMock()
        self.shell.close()
        self.shell._client.close.assert_called_once()

    @patch('jnpr.junos.utils.start_shell.StartShell.wait_for')
    def test_startshell_run(self, mock_wait):
        self.shell._chan = MagicMock()
        self.shell.run('ls')
        self.assertTrue(call.send('echo $?') in self.shell._chan.mock_calls)

    @patch('jnpr.junos.utils.start_shell.select')
    def test_startshell_wait_for(self, mock_select):
        mock_select.return_value = ['> ', 2, 3]
        self.shell._chan = MagicMock()
        self.assertTrue(call.endswith('> ') in self.shell.wait_for('> ')[0].mock_calls)

    @patch('jnpr.junos.utils.start_shell.StartShell.open')
    @patch('jnpr.junos.utils.start_shell.StartShell.close')
    def test_startshell_context(self, mock_open, mock_close):
        with StartShell(self.dev) as shell:
            shell._chan = MagicMock()
            shell.send('test')
            mock_close.assert_called_once(call())
