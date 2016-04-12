__author__ = "Rick Sherman, Nitin Kumar"
__credits__ = "Jeremy Schulman"

import sys
from six import StringIO
from contextlib import contextmanager

import unittest
from nose.plugins.attrib import attr

from jnpr.junos import Device
from jnpr.junos.utils.scp import SCP

from mock import patch
import sys
if sys.version<'3':
    builtin_string = '__builtin__'
else:
    builtin_string = 'builtins'

@attr('unit')
class TestScp(unittest.TestCase):
    def setUp(self):
        self.dev = Device(host='1.1.1.1')

    @patch('paramiko.SSHClient')
    def test_scp_open(self, mock_connect):
        from scp import SCPClient
        self.dev.bind(scp=SCP)
        assert isinstance(self.dev.scp.open(), SCPClient)

    @patch('paramiko.SSHClient')
    def test_scp_close(self, mock_connect):
        self.dev.bind(scp=SCP)
        self.dev.scp.open()
        self.assertEqual(self.dev.scp.close(), None)

    @patch('paramiko.SSHClient')
    def test_scp_context(self, mock_connect):
        with SCP(self.dev) as scp:
            scp.get('addrbook.conf')

    @patch('jnpr.junos.device.os')
    @patch(builtin_string + '.open')
    @patch('paramiko.config.SSHConfig.lookup')
    @patch('paramiko.SSHClient')
    @patch('paramiko.proxy.ProxyCommand')
    def test_scp_proxycommand(self, os_mock, open_mock, mock_paramiko,
                              mock_connect, mock_proxy):
        os_mock.path.exists.return_value = True
        self.dev._sshconf_path = '/home/rsherman/.ssh/config'
        with SCP(self.dev) as scp:
            scp.get('addrbook.conf')
        mock_proxy.assert_called_any()

    def test_scp_progress(self):
        scp = SCP(self.dev)
        print (scp._scp_progress('test', 100, 50))

    @patch('paramiko.SSHClient')
    @patch('scp.SCPClient.put')
    @patch('scp.SCPClient.__init__')
    def test_scp_user_def_progress(self, mock_scpclient, mock_put, mock_ssh):
        mock_scpclient.return_value = None

        def fn(file, total, tfd):
            pass
        package = 'test.tgz'
        with SCP(self.dev, progress=fn) as scp:
            scp.put(package)
        self.assertEqual(
            mock_scpclient.mock_calls[0][2]['progress'].__name__, 'fn')

    @patch('paramiko.SSHClient')
    @patch('scp.SCPClient.put')
    @patch('scp.SCPClient.__init__')
    def test_scp_user_def_progress_args_2(self, mock_scpclient, mock_put,
                                          mock_ssh):
        mock_scpclient.return_value = None

        def myprogress(dev, report):
            print ("host: %s, report: %s" % (dev.hostname, report))
        package = 'test.tgz'
        with SCP(self.dev, progress=myprogress) as scp:
            scp.put(package)
        self.assertEqual(
            mock_scpclient.mock_calls[0][2]['progress'].__name__, '_scp_progress')

    @patch('paramiko.SSHClient')
    @patch('scp.SCPClient.put')
    @patch('scp.SCPClient.__init__')
    def test_scp_progress_true(self, mock_scpclient, mock_put, mock_sshclient):
        mock_scpclient.return_value = None
        package = 'test.tgz'
        with SCP(self.dev, progress=True) as scp:
            scp.put(package)
        self.assertEqual(mock_scpclient.mock_calls[0][2]['progress'].__name__,
                         '_scp_progress')

    @contextmanager
    def capture(self, command, *args, **kwargs):
        out, sys.stdout = sys.stdout, StringIO()
        command(*args, **kwargs)
        sys.stdout.seek(0)
        yield sys.stdout.read()
        sys.stdout = out
