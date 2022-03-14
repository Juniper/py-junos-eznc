__author__ = "rsherman, vnitinv"

import unittest
from nose.plugins.attrib import attr

from jnpr.junos import Device


@attr("functional")
class TestDeviceSsh(unittest.TestCase):
    def tearDown(self):
        self.dev.close()

    def test_device_open_key_pass(self):
        self.dev = Device(
            host="10.209.14.76",
            user="root",
            # ssh_private_key_file="/var/lib/jenkins/.ssh/passkey",
            passwd="Embe1mpls",
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)
