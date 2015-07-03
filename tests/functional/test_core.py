'''

@author: rsherman
'''
import unittest2 as unittest
from nose.plugins.attrib import attr
from jnpr.junos.exception import RpcTimeoutError


@attr('functional')
class TestCore(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        from jnpr.junos import Device
        self.dev = Device(host='pabst.englab.juniper.net',
                          user='jenkins', password='password123')
        self.dev.open()

    @classmethod
    def tearDownClass(self):
        self.dev.close()

    def test_device_open(self):
        self.assertEqual(self.dev.connected, True)

    def test_device_facts(self):
        assert self.dev.facts['hostname'] == 'pabst'

    def test_device_get_timeout(self):
        assert self.dev.timeout == 30

    def test_device_set_timeout(self):
        self.dev.timeout = 35
        assert self.dev.timeout == 35

    def test_device_cli(self):
        self.assertTrue('srx210' in self.dev.cli('show version'))

    def test_device_rpc(self):
        res = self.dev.rpc.traceroute(noresolve=True, host='8.8.8.8', wait='1')
        self.assertEqual(res.tag, 'traceroute-results')

    def test_device_rpc_timeout(self):
        with self.assertRaises(RpcTimeoutError):
            self.dev.rpc.traceroute(noresolve=True, host='8.8.8.8', dev_timeout=1)

    def test_device_rpc_normalize_true(self):
        rsp = self.dev.rpc.get_interface_information(interface_name='ge-0/0/0', normalize=True)
        self.assertEqual(rsp.xpath('physical-interface/name')[0].text, 'ge-0/0/0')

    def test_device_rpc_normalize_false(self):
        rsp = self.dev.rpc.get_interface_information(interface_name='ge-0/0/0', normalize=False)
        self.assertEqual(rsp.xpath('physical-interface/name')[0].text, '\nge-0/0/0\n')
