__author__ = "Aaron-MJohn"

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import os
import tempfile

from jnpr.junos import Device
from jnpr.junos.utils.scp import SCP
from jnpr.junos.utils.start_shell import StartShell


class TestScp(unittest.TestCase):
    def test_scp_put_with_look_for_keys_disabled(self):
        dev = Device(
            host="x.x.x.x",
            user="netops",
            passwd="net123",
            look_for_keys=False,
        )
        remote_path = "/var/tmp/test_scp_look_for_keys_disabled.txt"

        with tempfile.NamedTemporaryFile("w", delete=False) as local_file:
            local_file.write("scp functional test\n")
            local_path = local_file.name

        try:
            dev.open()

            with SCP(dev) as scp:
                scp.put(local_path, remote_path)

            with StartShell(dev) as sh:
                ok, output = sh.run("cat {}".format(remote_path))
                self.assertTrue(ok)
                self.assertIn("scp functional test", output)
        finally:
            if dev.connected:
                try:
                    with StartShell(dev) as sh:
                        sh.run("rm -f {}".format(remote_path))
                finally:
                    dev.close()
            os.unlink(local_path)

    def test_scp_put_with_allow_agent_disabled(self):
        dev = Device(
            host="x.x.x.x",
            user="netops",
            passwd="net123",
            allow_agent=False,
        )
        remote_path = "/var/tmp/test_scp_allow_agent_disabled.txt"

        with tempfile.NamedTemporaryFile("w", delete=False) as local_file:
            local_file.write("scp functional test\n")
            local_path = local_file.name

        try:
            dev.open()

            with SCP(dev) as scp:
                scp.put(local_path, remote_path)

            with StartShell(dev) as sh:
                ok, output = sh.run("cat {}".format(remote_path))
                self.assertTrue(ok)
                self.assertIn("scp functional test", output)
        finally:
            if dev.connected:
                try:
                    with StartShell(dev) as sh:
                        sh.run("rm -f {}".format(remote_path))
                finally:
                    dev.close()
            os.unlink(local_path)
