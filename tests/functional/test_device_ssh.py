__author__ = "rsherman, vnitinv"

import unittest
from nose.plugins.attrib import attr

from jnpr.junos import Device


@attr('functional')
class TestDeviceSsh(unittest.TestCase):

    def tearDown(self):
        self.dev.close()

    # def test_device_open_default_key(self):
    #     self.dev = Device(host='highlife.englab.juniper.net', user='jenkins')
    #     self.dev.open()
    #     self.assertEqual(self.dev.connected, True)

    def test_device_open_key_pass(self):
        self.dev = Device(host='highlife.englab.juniper.net', user='jenkins',
                          ssh_private_key_file='/var/lib/jenkins/.ssh/passkey',
                          passwd='password')
        self.dev.open()
        self.assertEqual(self.dev.connected, True)
