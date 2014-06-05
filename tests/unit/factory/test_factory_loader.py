__author__ = "Rick Sherman, Nitin Kumar"
__credits__ = "Jeremy Schulman"

import unittest
from lxml import etree
from nose.plugins.attrib import attr
from jnpr.junos.factory import FactoryLoader
from jnpr.junos.op.routes import RouteTable
from jnpr.junos import Device
from mock import patch


@attr('unit')
class TestFactoryLoader(unittest.TestCase):

    def setUp(self):
        self.fl = FactoryLoader()
        # self.dev = Device(host='1.1.1.1', user='rick', password='password123',
        #           gather_facts=False)
        # from jnpr.junos.op.routes import RouteTable
        # routes = RouteTable(self.dev)
        self.fl.catalog = {'RouteTable':
                           {'item': 'route-table/rt',
                            'rpc': 'get-route-information',
                            'args_key': 'destination',
                            'key': 'rt-destination',
                            'view': 'RouteTableView'}}

        self.fl._catalog_dict = {'RouteTableView': {'groups': {'entry': 'rt-entry'},
                                                    'fields_entry': {'via': 'nh/via | nh/nh-local-interface',
                                                                     'age': {'age/@seconds': 'int'},
                                                                     'nexthop': 'nh/to',
                                                                     'protocol': 'protocol-name'},
                                                    'extends': 'test'}}

    def test_FactoryLoader__build_optable(self):
        self.assertEqual(self.fl._build_optable('RouteTable'),
                         self.fl.catalog['RouteTable'])

    def test_FactoryLoader__build_cfgtable(self):
        self.assertEqual(self.fl._build_cfgtable('RouteTable'),
                         self.fl.catalog['RouteTable'])

    @patch('jnpr.junos.factory.factory_loader._VIEW')
    def test_FactoryLoader__build_view(self, mock_view):
        mock_view.return_value = type('test', (object,), {})
        self.assertEqual(self.fl._build_view('RouteTableView'),
                         self.fl.catalog['RouteTableView'])
