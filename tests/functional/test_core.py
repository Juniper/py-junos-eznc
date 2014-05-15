'''

@author: rsherman
'''
import unittest
from nose.plugins.attrib import attr


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
        sw = self.dev.rpc.get_software_information()
        hostname = sw.findtext('.//host-name')
        self.assertEqual(hostname, 'pabst')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'TestCore.testName']
    unittest.main()
