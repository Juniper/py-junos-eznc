__author__ = "rsherman, vnitinv"

from jnpr.junos import Device

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestDeviceSsh(unittest.TestCase):
    def tearDown(self):
        self.dev.close()

    def test_device_open_key_pass(self):
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            ssh_private_key_file="~/.ssh/id_rsa",
            passwd="net123",
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_password(self):
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            passwd="net123",
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_ssh_agent_true(self):
        self.dev = Device(host="x.x.x.x", user="netops", allow_agent=True)
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_ssh_agent_false(self):
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            allow_agent=False,
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_key_file(self):
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            ssh_private_key_file="~/.ssh/id_rsa",
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_key_file(self):
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            ssh_private_key_file="~/.ssh/id_rsa",
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_proxy(self):
        self.dev = Device(
            host="x.x.x.x", user="netops", proxy_command="ssh -J netops@y.y.y.y"
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_ssh_agent_proxy(self):
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            proxy_command="ssh -J netops@y.y.y.y",
            allow_agent=True,
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_key_file_proxy(self):
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            proxy_command="ssh -J netops@y.y.y.y",
            ssh_private_key_file="~/.ssh/id_rsa",
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_ssh_agent_proxy(self):
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            proxy_command="ssh -J netops@y.y.y.y",
            allow_agent=True,
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_key_file_proxy(self):
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            proxy_command="ssh -J netops@y.y.y.y",
            ssh_private_key_file="~/.ssh/id_rsa",
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)
