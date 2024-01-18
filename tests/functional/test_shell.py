__author__ = "jnpr-community-netdev"

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import yaml


class test(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        from jnpr.junos import Device

        with open("config.yaml", "r") as fyaml:
            cfg = yaml.safe_load(fyaml)
        self.dev = Device(**cfg)
        self.dev.open()

    @classmethod
    def tearDownClass(self):
        self.dev.close()

    def test_shell_run(self):
        from jnpr.junos.utils.start_shell import StartShell

        with StartShell(self.dev) as sh:
            output = sh.run("pwd")
            self.assertTrue(output[0])

    def test_shell_run_with_sleep(self):
        from jnpr.junos.utils.start_shell import StartShell

        with StartShell(self.dev) as sh:
            output = sh.run("hostname", sleep=2)
            self.assertTrue(output[0])

    def test_shell_run_shell_type_ssh(self):
        from jnpr.junos.utils.start_shell import StartShell

        with StartShell(self.dev, shell_type="ssh") as sh:
            output = sh.run("hostname", sleep=2)
            self.assertTrue(output[0])

    def test_shell_run_shell_type_csh(self):
        from jnpr.junos.utils.start_shell import StartShell

        with StartShell(self.dev, shell_type="csh") as sh:
            output = sh.run("hostname", sleep=2)
            self.assertTrue(output[0])
