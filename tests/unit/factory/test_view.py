__author__ = "Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr

from jnpr.junos import Device
from jnpr.junos.factory.view import View
from jnpr.junos.op.phyport import PhyPortTable

from lxml import etree


@attr('unit')
class TestFactoryView(unittest.TestCase):

    def setUp(self):
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                  gather_facts=False)
        self.ppt = PhyPortTable(self.dev)

        ret_val = '<physical-interface> \
            <name>ge-0/0/0</name> \
            <admin-status>up</admin-status> \
            <oper-status>up</oper-status> \
        </physical-interface>'
        xml = etree.fromstring(ret_val)
        self.v = View(self.ppt, xml)

    def test_view_init(self):
        self.assertEqual(self.v.key, 'ge-0/0/0')

    def test_view_init_multi_exception(self):
        self.assertRaises(ValueError, View, self.ppt, ['test', '123'])

    def test_view_init_lxml_exception(self):
        self.assertRaises(ValueError, View, self.ppt, ['test'])

    def test_view_repr(self):
        self.assertEqual(str(self.v), 'View:ge-0/0/0')

    def test_view_d(self):
        self.assertEqual(self.v.D, self.dev)

    def test_view_name(self):
        self.assertEqual(self.v.name, 'ge-0/0/0')

    def test_view_name_xpath_none(self):
        self.v.ITEM_NAME_XPATH = None
        self.assertEqual(self.v.name, '1.1.1.1')

    def test_view_name_xpath_composite(self):
        self.v.ITEM_NAME_XPATH = ['name', 'admin-status']
        self.assertEqual(self.v.name, ('ge-0/0/0', 'up'))
