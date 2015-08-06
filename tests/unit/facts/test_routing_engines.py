__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr
from mock import patch, MagicMock
import os

from jnpr.junos import Device
from jnpr.junos.facts.routing_engines import facts_routing_engines as routing_engines

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


@attr('unit')
class TestRoutingEngines(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()
        self.facts = {}
        self.mode = ''
        self.vc = False
        self.vct = False
        self.vcf = False

    @patch('jnpr.junos.Device.execute')
    def test_multi_re_vc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.mode = 'multi'
        self.vc = True
        routing_engines(self.dev, self.facts)
        self.assertTrue(self.facts['vc_capable'])
        self.assertTrue(self.facts['2RE'])
        self.assertEqual(self.facts['RE0-RE1']['mastership_state'], 'backup')

    # This test is for an issue where a MX may return nothing for the vc rpc
    @patch('jnpr.junos.Device.execute')
    def test_vc_info_true(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.mode = 'multi'
        self.vc = True
        self.vct = True
        routing_engines(self.dev, self.facts)
        self.assertFalse(self.facts['vc_capable'])
        self.assertTrue(self.facts['2RE'])
        self.assertEqual(self.facts['RE1']['mastership_state'], 'backup')

    @patch('jnpr.junos.Device.execute')
    def test_mixed_mode_vcf(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.mode = 'multi'
        self.vc = True
        self.vcf = True
        routing_engines(self.dev, self.facts)
        self.assertTrue(self.facts['vc_fabric'])
        self.assertEqual(self.facts['vc_mode'], 'Mixed')

    @patch('jnpr.junos.Device.execute')
    def test_multi_instance(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.mode = 'multi'
        routing_engines(self.dev, self.facts)
        self.assertTrue(self.facts['2RE'])

    @patch('jnpr.junos.Device.execute')
    def test_master(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.mode = 'master'
        routing_engines(self.dev, self.facts)
        self.assertEqual(self.facts['RE0']['mastership_state'], 'master')

    @patch('jnpr.junos.Device.execute')
    def test_routing_engine_exception_ret_none(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.dev.rpc.get_route_engine_information = MagicMock(side_effect=ValueError)
        self.assertEqual(routing_engines(self.dev, self.facts), None)

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(foo, self.dev._conn.
                              _device_handler.transform_reply()).\
            _NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        if args:
            if self.vc is True and args[0].tag == 'get-virtual-chassis-information':
                if self.vct is True:
                    return True
                elif self.vcf is True:
                    return self._read_file('get-virtual-chassis-information_mmvcf.xml')
                else:
                    return self._read_file('get-virtual-chassis-information.xml')
            return self._read_file(args[0].tag + '_' + self.mode + '.xml')
