__author__ = "Rick Sherman"

import unittest2 as unittest
from nose.plugins.attrib import attr

from jnpr.junos.op.lldp import LLDPNeighborTable


@attr('functional')
class TestTable(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        from jnpr.junos import Device
        self.dev = Device(host='stag.englab.juniper.net',
                          user='jenkins', password='password123')
        self.dev.open()

    @classmethod
    def tearDownClass(self):
        self.dev.close()

    def test_table_union(self):
        lldp = LLDPNeighborTable(self.dev)
        lldp.get('et-0/1/1')
        self.assertEqual(lldp['et-0/1/1'].local_int, 'et-0/1/1')

    def test_table_json(self):
        lldp = LLDPNeighborTable(self.dev)
        lldp.get('et-0/1/1')
        json = '{"et-0/1/1": {"remote_port_desc": "et-1/1/1", '\
            '"local_int": "et-0/1/1", "remote_sysname": "highlife", '\
            '"local_parent": "-", "remote_chassis_id": "4c:96:14:f3:d5:20", '\
            '"remote_type": "Mac address"}}'
        self.assertEqual(lldp.to_json(), json)
