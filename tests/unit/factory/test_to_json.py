__author__ = "Rick Sherman"

import unittest2 as unittest
from nose.plugins.attrib import attr
from mock import patch
import os
import json

from jnpr.junos import Device
from jnpr.junos.factory.to_json import PyEzJSONEncoder, TableJSONEncoder, TableViewJSONEncoder
from jnpr.junos.op.routes import RouteSummaryTable
from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


@attr('unit')
class TestToJson(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()

    def test_pyez_encoder_default(self):
        with self.assertRaises(TypeError):
            PyEzJSONEncoder.default(PyEzJSONEncoder(), 'test')

    def test_table_encoder_default(self):
        with self.assertRaises(TypeError):
            TableJSONEncoder.default(TableJSONEncoder(), 'test')

    def test_view_encoder_default(self):
        with self.assertRaises(TypeError):
            TableViewJSONEncoder.default(TableViewJSONEncoder(), 'test')

    @patch('jnpr.junos.Device.execute')
    def test_table_json(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        rst = RouteSummaryTable(self.dev)
        rst.get()
        resp = rst.to_json()
        j = {'ISP-1.inet.0': {'proto': {'Local': {'count': 1, 'active': 1}, 'Direct': {'count': 3, 'active': 3}},
                              'dests': 4, 'holddown': 0, 'active': 4, 'hidden': 0, 'total': 4},
             'ISP-2.inet.0': {'proto': {'Local': {'count': 1, 'active': 1}, 'Direct': {'count': 3, 'active': 3}},
                              'dests': 4, 'holddown': 0, 'active': 4, 'hidden': 0, 'total': 4},
             'inet.0': {'proto': {'Local': {'count': 4, 'active': 4}, 'Static': {'count': 1, 'active': 1},
                                  'Direct': {'count': 4, 'active': 3}}, 'dests': 8, 'holddown': 0, 'active': 8,
                        'hidden': 0, 'total': 9}}
        self.assertEqual(eval(resp), j)

    @patch('jnpr.junos.Device.execute')
    def test_view_json(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        rst = RouteSummaryTable(self.dev)
        rst.get()
        resp = rst["ISP-1.inet.0"].to_json()
        j = {"ISP-1.inet.0": {"proto": {"Local": {"count": 1, "active": 1}, "Direct": {"count": 3, "active": 3}},
                              "dests": 4, "holddown": 0, "active": 4, "hidden": 0, "total": 4}}
        self.assertEqual(eval(resp), j)

    @patch('jnpr.junos.Device.execute')
    def test_json_rpc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        resp = self.dev.rpc.get_software_information()
        j = {'package-information': {'comment': 'JUNOS Software Release [12.1X46-D15.3]', 'name': 'junos'},
             'host-name': 'firefly', 'product-model': 'firefly-perimeter', 'product-name': 'firefly-perimeter'}
        self.assertEqual(eval(json.dumps(resp)), j)

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(foo, self.dev._conn.
                              _device_handler.transform_reply())\
            ._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            if 'normalize' in kwargs and args:
                return self._read_file(args[0].tag + '.xml')
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        if args:
            return self._read_file(args[0].tag + '.xml')
