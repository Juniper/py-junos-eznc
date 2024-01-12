__author__ = "rsherman, vnitinv"

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from jnpr.junos.exception import RpcTimeoutError


class TestCore(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        from jnpr.junos import Device

        self.dev = Device(host="xxxx", user="jenkins", password="password")
        self.dev.open()

    @classmethod
    def tearDownClass(self):
        self.dev.close()

    def test_device_open(self):
        self.assertEqual(self.dev.connected, True)

    def test_device_facts(self):
        assert self.dev.facts["hostname"] == "highlife"

    def test_device_get_timeout(self):
        assert self.dev.timeout == 30

    def test_device_set_timeout(self):
        self.dev.timeout = 35
        assert self.dev.timeout == 35

    def test_device_cli(self):
        self.assertTrue("qfx5100" in self.dev.cli("show version"))

    def test_device_rpc(self):
        res = self.dev.rpc.get_route_information(destination="10.48.21.71")
        self.assertEqual(res.tag, "route-information")

    def test_device_rpc_format_text(self):
        res = self.dev.rpc.get_interface_information({"format": "text"})
        self.assertEqual(res.tag, "output")

    def test_device_rpc_timeout(self):
        with self.assertRaises(RpcTimeoutError):
            self.dev.rpc.get_route_information(dev_timeout=0.01)

    def test_device_rpc_normalize_true(self):
        rsp = self.dev.rpc.get_interface_information(
            interface_name="ge-0/0/1", normalize=True
        )
        self.assertEqual(rsp.xpath("physical-interface/name")[0].text, "ge-0/0/1")

    def test_load_config(self):
        from jnpr.junos.utils.config import Config

        cu = Config(self.dev)
        data = """interfaces {
           ge-1/0/0 {
              description "MPLS interface";
              unit 0 {
                 family mpls;
              }
          }
        }
        """
        cu.load(data, format="text")
        self.assertTrue(cu.commit_check())
        if cu.commit_check():
            cu.rollback()
