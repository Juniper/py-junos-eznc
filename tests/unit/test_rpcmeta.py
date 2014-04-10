__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr

from jnpr.junos.device import Device
from jnpr.junos.rpcmeta import _RpcMetaExec

from mock import patch
from lxml import etree


@attr('unit')
class Test_RpcMetaExec(unittest.TestCase):

    def setUp(self):
        self.dev = Device(host='1.1.1.1')
        self.rpc = _RpcMetaExec(self.dev)

    def test_rpcmeta_constructor(self):
        self.assertIsInstance(self.rpc._junos, Device)

    @patch('jnpr.junos.device.Device.execute')
    def test_rpcmeta_load_config_option(self, mock_execute_fn):
        root = etree.XML('<root><a>test</a></root>')
        self.rpc.load_config(root)

    @patch('jnpr.junos.device.Device.execute')
    def test_rpcmeta_load_config_option_action(self, mock_execute_fn):
        set_commands="""
            set system host-name test_rpc
            set system domain-name test.juniper.net
        """
        self.rpc.load_config(set_commands, action='set')

    @patch('jnpr.junos.device.Device.execute')
    def test_rpcmeta_option_format(self, mock_execute_fn):
        set_commands="""
            set system host-name test_rpc
            set system domain-name test.juniper.net
        """
        self.rpc.load_config(set_commands, format='text')

    @patch('jnpr.junos.device.Device.execute')
    def test_rpcmeta_exec_rpc_vargs(self, mock_execute_fn):
        self.rpc.system_users_information(dict(format='text'))

    @patch('jnpr.junos.device.Device.execute')
    def test_rpcmeta_exec_rpc_kvargs(self, mock_execute_fn):
        self.rpc.system_users_information(set_data=('test',))
