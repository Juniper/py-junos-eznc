__author__ = "rsherman, vnitinv"

import unittest2 as unittest
from nose.plugins.attrib import attr

from jnpr.junos.op.routes import RouteTable
import json


@attr('functional')
class TestTable(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        from jnpr.junos import Device
        self.dev = Device(host='highlife.englab.juniper.net',
                          user='jenkins', password='password123')
        self.dev.open()

    @classmethod
    def tearDownClass(self):
        self.dev.close()

    def test_table_union(self):
        tbl = RouteTable(self.dev)
        tbl.get()
        self.assertEqual(tbl[0].via, 'em0.0')

    def test_table_json(self):
        tbl = RouteTable(self.dev)
        tbl.get('10.48.21.71')
        self.assertEqual(
            json.loads(tbl.to_json())["10.48.21.71/32"]["protocol"],
            "Local")
