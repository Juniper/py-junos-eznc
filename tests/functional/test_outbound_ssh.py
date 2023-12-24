__author__ = "mwiget"

import unittest

import socket
from jnpr.junos import Device


class TestDeviceSsh(unittest.TestCase):
    def tearDown(self):
        self.dev.close()

    def test_device_open_key_pass(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = 2200
        s.bind(("", port))
        s.listen(5)
        print("\nListening on port %d for incoming sessions ..." % (port))
        sock_fd = 0
        while True:
            client, addr = s.accept()
            print("Got a connection from %s:%d!" % (addr[0], addr[1]))
            sock_fd = self.__launch_junos_proxy(client, addr)

            print("Logging in ...")

            self.dev = Device(
                host=None,
                sock_fd=sock_fd,
                user="jenkins",
                ssh_private_key_file="/var/lib/jenkins/.ssh/passkey",
                passwd="password123",
            )

            print("requesting info...")
            self.dev.open()
            self.assertEqual(self.dev.connected, True)
            print("Hostname is %s" % (self.dev.facts["hostname"]))
            assert self.dev.facts["hostname"] == "highlife"
            break

    def __launch_junos_proxy(self, client, addr):
        val = {"MSG-ID": None, "MSG-VER": None, "DEVICE-ID": None}
        msg = ""
        count = 3
        while len(msg) < 100 and count > 0:
            c = client.recv(1)
            if c == "\r":
                continue

            if c == "\n":
                count -= 1
                if msg.find(":"):
                    (key, value) = msg.split(": ")
                    val[key] = value
                    msg = ""
            else:
                msg += c

        print("MSG %s %s %s" % (val["MSG-ID"], val["MSG-VER"], val["DEVICE-ID"]))
        return client.fileno()
