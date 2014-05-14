__author__ = "Rick Sherman"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import unittest
from nose.plugins.attrib import attr

from jnpr.junos import Device
from jnpr.junos.utils.scp import SCP

from mock import patch


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
