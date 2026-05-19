__author__ = "rsherman, vnitinv"

from jnpr.junos import Device

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestDeviceSsh(unittest.TestCase):
    def tearDown(self):
        if hasattr(self, "dev") and self.dev.connected:
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

    # ------------------------------------------------------------------
    # proxy_command tests
    # ------------------------------------------------------------------

    def test_device_open_no_proxy_ssh_config_devnull(self):
        """Direct connection (no proxy_command) with ssh_config suppressed
        via /dev/null to ensure no host-level ProxyCommand is picked up."""
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            port=22,
            ssh_private_key_file="~/.ssh/id_rsa",
            ssh_config="/dev/null",
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_proxy(self):
        """proxy_command using ssh -W %h:%p through a jump host, combined
        with an explicit SSH private key file and port=22."""
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            port=22,
            ssh_private_key_file="~/.ssh/id_rsa",
            proxy_command="ssh -W %h:%p -q netops@y.y.y.y",
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_proxy_with_ssh_agent(self):
        """proxy_command with ssh-agent forwarding enabled."""
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            port=22,
            proxy_command="ssh -W %h:%p -q netops@y.y.y.y",
            allow_agent=True,
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_proxy_allow_agent_false(self):
        """proxy_command with ssh-agent forwarding explicitly disabled."""
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            port=22,
            ssh_private_key_file="~/.ssh/id_rsa",
            proxy_command="ssh -W %h:%p -q netops@y.y.y.y",
            allow_agent=False,
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_open_proxy_default_port(self):
        """proxy_command without an explicit port; %p expands to the
        default NETCONF port (830)."""
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            ssh_private_key_file="~/.ssh/id_rsa",
            proxy_command="ssh -W %h:%p -q netops@y.y.y.y",
        )
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

    def test_device_proxy_command_stored_on_instance(self):
        """The proxy_command string is preserved on the Device instance."""
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            port=22,
            ssh_private_key_file="~/.ssh/id_rsa",
            proxy_command="ssh -W %h:%p -q netops@y.y.y.y",
        )
        self.assertEqual(self.dev._proxy_command, "ssh -W %h:%p -q netops@y.y.y.y")

    def test_device_proxy_empty_string_not_used(self):
        """An empty proxy_command string should not activate proxy routing."""
        self.dev = Device(
            host="x.x.x.x",
            user="netops",
            proxy_command="",
        )
        self.assertFalse(self.dev._proxy_command)

    def test_device_proxy_and_sock_fd_raises(self):
        """Combining proxy_command with sock_fd must raise ValueError."""
        with self.assertRaises(ValueError):
            Device(
                host="x.x.x.x",
                user="netops",
                proxy_command="ssh -W %h:%p -q netops@y.y.y.y",
                sock_fd=5,
            )
