__author__ = "Rick Sherman, Nitin Kumar"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr
from mock import MagicMock
from jnpr.junos import Device
from jnpr.junos.factory.view import View
from jnpr.junos.op.phyport import PhyPortStatsTable, PhyPortStatsView
from lxml import etree


@attr('unit')
class TestFactoryView(unittest.TestCase):

    def setUp(self):
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.ppt = PhyPortStatsTable(self.dev)

        ret_val = '<physical-interface> \
            <name>ge-0/0/0</name> \
            <admin-status>up</admin-status> \
            <oper-status>up</oper-status> \
        </physical-interface>'
        xml = etree.fromstring(ret_val)
        self.v = PhyPortStatsView(self.ppt, xml)

    def test_view_init(self):
        self.assertEqual(self.v.key, 'ge-0/0/0')

    def test_view_init_multi_exception(self):
        self.assertRaises(ValueError, View, self.ppt, ['test', '123'])

    def test_view_init_lxml_exception(self):
        self.assertRaises(ValueError, View, self.ppt, ['test'])

    def test_view_repr(self):
        self.assertEqual(str(self.v), 'PhyPortStatsView:ge-0/0/0')

    def test_view_d(self):
        self.assertEqual(self.v.D, self.dev)

    def test_view_name(self):
        self.assertEqual(self.v.name, 'ge-0/0/0')

    def test_view_name_xpath_none(self):
        self.v.ITEM_NAME_XPATH = None
        self.assertEqual(self.v.name, '1.1.1.1')

    def test_view_name_xpath_composite(self):
        self.v.ITEM_NAME_XPATH = ['name', 'missing', 'admin-status']
        self.assertEqual(self.v.name, ('ge-0/0/0', None, 'up'))

    def test_view_asview(self):
        self.assertEqual(
            type(
                self.v.asview(PhyPortStatsTable)),
            PhyPortStatsTable)

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

    def test_view_updater_context(self):
        with self.v.updater(fields=False) as up:
            self.assertEqual(up.__class__.__name__, 'RunstatViewMore')

    def test_view_updater_fields_true(self):
        def fn():
            with self.v.updater(fields=True):
                pass
        fn()
        self.assertEqual(
            self.v.GROUPS, {
                'rxerrs': 'input-error-list', 'ts': 'traffic-statistics'})

    def test_view_updater_groups_true(self):
        def fn():
            with self.v.updater(groups=True):
                pass
        fn()
        self.assertEqual(
            self.v.GROUPS, {
                'rxerrs': 'input-error-list', 'ts': 'traffic-statistics'})

    def test_view_updater_all_false(self):
        with self.v.updater(all=False):
            self.assertEqual(
                self.v.GROUPS, {
                    'rxerrs': 'input-error-list', 'ts': 'traffic-statistics'})

    def test_view_updater_with_groups_all_true(self):
        def fn():
            with self.v.updater(all=True) as more:
                more.groups = {}
        fn()
        self.assertEqual(
            self.v.GROUPS, {
                'rxerrs': 'input-error-list', 'ts': 'traffic-statistics'})

    def test_view_updater_with_groups_all_false(self):
        def fn():
            with self.v.updater(all=False) as more:
                more.groups = {}
        fn()
        self.assertEqual(
            self.v.GROUPS, {
                'rxerrs': 'input-error-list', 'ts': 'traffic-statistics'})

    def test_view___getattr__table_item(self):
        tbl = {'RouteTable': {'item': 'route-table/rt',
                              'rpc': 'get-route-information',
                              'args_key': 'destination',
                              'key': 'rt-destination',
                              'view': 'RouteTableView',
                              'table': PhyPortStatsTable}}
        self.v.FIELDS.update(tbl)
        self.assertEqual(self.v.RouteTable.__class__.__name__,
                         'PhyPortStatsTable')

    def test_view___getattr___munch(self):
        ret_val = '<physical-interface> \
            <name>ge-0/0/0</name> \
            <admin-status>up</admin-status> \
            <admin-status>down</admin-status> \
            <oper-status>up</oper-status> \
        </physical-interface>'
        xml = etree.fromstring(ret_val)
        self.v = PhyPortStatsView(self.ppt, xml)
        tbl = {'RouteTable': {'item': 'route-table/rt',
                              'rpc': 'get-route-information',
                              'args_key': 'destination',
                              'key': 'rt-destination',
                              'view': 'RouteTableView',
                              'xpath': './/admin-status'}}
        self.v.FIELDS.update(tbl)
        self.assertEqual(self.v.RouteTable, ['up', 'down'])

    def test_view___getattr___munch_tag(self):
        ret_val = '<physical-interface> \
            <name>ge-0/0/0</name> \
            <admin-status><test>test_tag</test></admin-status> \
            <oper-status>up</oper-status> \
        </physical-interface>'
        xml = etree.fromstring(ret_val)
        self.v = PhyPortStatsView(self.ppt, xml)
        tbl = {'RouteTable': {'item': 'route-table/rt',
                              'rpc': 'get-route-information',
                              'args_key': 'destination',
                              'key': 'rt-destination',
                              'view': 'RouteTableView',
                              'xpath': './/admin-status'}}
        self.v.FIELDS.update(tbl)
        self.assertEqual(self.v.RouteTable, 'admin-status')

    def test_view___getattr___raise_RuntimeError(self):
        ret_val = '<physical-interface> \
            <name>ge-0/0/0</name> \
            <admin-status><test>test_tag</test></admin-status> \
            <oper-status>up</oper-status> \
        </physical-interface>'
        xml = etree.fromstring(ret_val)
        self.v = PhyPortStatsView(self.ppt, xml)
        tbl = {'RouteTable': {'item': 'route-table/rt',
                              'rpc': 'get-route-information',
                              'args_key': 'destination',
                              'key': 'rt-destination',
                              'view': 'RouteTableView',
                              'xpath': './/admin-status',
                              'astype': 'abc'}}
        self.v.FIELDS.update(tbl)

        def fn():
            return self.v.RouteTable
        self.assertRaises(RuntimeError, fn)
