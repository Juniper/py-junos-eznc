__author__ = "rsherman, vnitinv"

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from jnpr.junos.op.routes import RouteTable
import json


class TestTable(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        from jnpr.junos import Device

        self.dev = Device(host="xxxx", user="jenkins", password="password")
        self.dev.open()

    @classmethod
    def tearDownClass(self):
        self.dev.close()

    def test_table_union(self):
        tbl = RouteTable(self.dev)
        tbl.get()
        self.assertEqual(tbl[0].via, "em0.0")

    def test_table_json(self):
        tbl = RouteTable(self.dev)
        tbl.get("10.48.21.71")
        self.assertEqual(
            json.loads(tbl.to_json())["10.48.21.71/32"]["protocol"], "Local"
        )
