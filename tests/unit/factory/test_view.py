__author__ = "Rick Sherman, Nitin Kumar"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr
from mock import MagicMock
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

    def test_view_asview(self):
        self.assertEqual(type(self.v.asview(PhyPortTable)), PhyPortTable)

    def test_view_refresh_can_refresh_false(self):
        self.v._table.can_refresh = False
        self.assertRaises(RuntimeError, self.v.refresh)

    def test_view_refresh_can_refresh_true(self):
        self.v._table.can_refresh = True
        self.v._table._rpc_get = MagicMock()
        self.v.refresh()
        self.v._table._rpc_get.assert_called_once_with('ge-0/0/0')

    def test_view___getattr__wrong_attr(self):
        try:
            self.v.abc
        except Exception as ex:
            self.assertEqual(ex.__class__, ValueError)

    def test_view_updater(self):
        with self.v.updater(fields=False) as up:
            self.assertEqual(up.__class__.__name__, 'RunstatViewMore')

    def test_view_updater_fields_true(self):
        def fn():
            with self.v.updater():
                pass
        self.assertRaises(NameError, fn)

    def test_view_updater_all_false(self):
        with self.v.updater(fields=False, all=False):
            self.assertEqual(self.v.FIELDS, {})