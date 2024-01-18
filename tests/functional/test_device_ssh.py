__author__ = "rsherman, vnitinv"

import unittest

from jnpr.junos import Device


class TestDeviceSsh(unittest.TestCase):
    def tearDown(self):
        self.dev.close()

    def test_device_open_key_pass(self):
        self.dev = Device(
            host="xxxx",
            user="jenkins",
            ssh_private_key_file="/var/lib/jenkins/.ssh/passkey",
            passwd="password",
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)
