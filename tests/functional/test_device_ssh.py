'''

@author: rsherman
'''
import unittest
from nose.plugins.attrib import attr

from jnpr.junos import Device


@attr('functional')
class TestDeviceSsh(unittest.TestCase):

    def tearDown(self):
        self.dev.close()

    def test_device_open_default_key(self):
        self.dev = Device('pabst.englab.juniper.net')
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_key_pass(self):
        self.dev = Device(host='pabst.englab.juniper.net', ssh_private_key_file='/var/lib/jenkins/.ssh/passkey', passwd='password')
        self.dev.open()
        self.assertEqual(self.dev.connected, True)
