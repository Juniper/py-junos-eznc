__author__ = "Stacy Smith"
__credits__ = "Jeremy Schulman, Nitin Kumar"

import unittest
from nose.plugins.attrib import attr
from mock import patch, MagicMock
import os
from lxml import etree

from jnpr.junos import Device
from jnpr.junos.exception import RpcError

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession


@attr('unit')
class TestGetSoftwareInformation(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager_setup
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()

    @patch('jnpr.junos.Device.execute')
    def test_sw_info_single(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_single
        self.assertEqual(self.dev.facts['junos_info']['re0']['text'],
                         '16.1R1.11')
        self.assertEqual(
            self.dev.facts['junos_info']['re0']['object'].as_tuple,
            (16, 1, 'R', '1', 11))
        self.assertEqual(self.dev.facts['hostname'],'r0')
        self.assertEqual(self.dev.facts['model'],'MX960')
        self.assertEqual(self.dev.facts['model_info'],{'re0': 'MX960'})
        self.assertEqual(self.dev.facts['version'],'16.1R1.11')
        self.assertEqual(self.dev.facts['version_info'].as_tuple,
                         (16, 1, 'R', '1', 11))
        self.assertEqual(self.dev.facts['version_RE0'],'16.1R1.11')
        self.assertEqual(self.dev.facts['version_RE1'],None)

    @patch('jnpr.junos.Device.execute')
    def test_sw_info_vc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_vc
        self.assertEqual(self.dev.facts['junos_info']['member0']['text'],
                         '15.1-20161209.0')
        self.assertEqual(
            self.dev.facts['junos_info']['member0']['object'].as_tuple,
            (15, 1, 'I', '20161209', '0'))
        self.assertEqual(self.dev.facts['junos_info']['member1']['text'],
                         '15.1-20161209.0')
        self.assertEqual(
            self.dev.facts['junos_info']['member1']['object'].as_tuple,
            (15, 1, 'I', '20161209', '0'))
        self.assertEqual(self.dev.facts['hostname'],'reefbreak1')
        self.assertEqual(self.dev.facts['model'],'MX240')
        self.assertEqual(self.dev.facts['model_info'],
                         {'member1': 'MX240', 'member0': 'MX240'})
        self.assertEqual(self.dev.facts['version'],'15.1-20161209.0')
        self.assertEqual(self.dev.facts['version_info'].as_tuple,
                         (15, 1, 'I', '20161209', '0'))
        self.assertEqual(self.dev.facts['version_RE0'],None)
        self.assertEqual(self.dev.facts['version_RE1'],None)


    @patch('jnpr.junos.Device.execute')
    def test_sw_info_simple(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_simple
        self.assertEqual(self.dev.facts['junos_info']['re0']['text'],
                         '12.3X48-D40.5')
        self.assertEqual(self.dev.facts['junos_info']['re0']['object'].as_tuple,
                         (12, 3, 'X', (48, 'D', 40), 5))
        self.assertEqual(self.dev.facts['hostname'],'lsys500')
        self.assertEqual(self.dev.facts['model'],'SRX3600')
        self.assertEqual(self.dev.facts['model_info'],{'re0': 'SRX3600'})
        self.assertEqual(self.dev.facts['version'],'12.3X48-D40.5')
        self.assertEqual(self.dev.facts['version_info'].as_tuple,
                         (12, 3, 'X', (48, 'D', 40), 5))
        self.assertEqual(self.dev.facts['version_RE0'],'12.3X48-D40.5')
        self.assertEqual(self.dev.facts['version_RE1'],None)

    @patch('jnpr.junos.Device.execute')
    def test_sw_info_no_version(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_no_version
        self.assertEqual(self.dev.facts['junos_info'],None)
        self.assertEqual(self.dev.facts['hostname'], 'lsys500')
        self.assertEqual(self.dev.facts['model'],'SRX3600')
        self.assertEqual(self.dev.facts['model_info'],{'re0': 'SRX3600'})
        self.assertEqual(self.dev.facts['version'],'0.0I0.0')
        self.assertEqual(self.dev.facts['version_RE0'],None)
        self.assertEqual(self.dev.facts['version_RE1'],None)

    @patch('jnpr.junos.Device.execute')
    def test_sw_info_dual(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_dual
        self.assertEqual(self.dev.facts['junos_info']['re0']['text'],
                         '15.1F5.15-C1.12')
        self.assertEqual(self.dev.facts['junos_info']['re1']['text'],
                         '15.1F5.15')
        self.assertEqual(self.dev.facts['hostname'], 'baku')
        self.assertEqual(self.dev.facts['model'],'MX480')
        self.assertEqual(self.dev.facts['model_info'],
                         {'re0': 'MX480', 're1': 'MX480'})
        self.assertEqual(self.dev.facts['version'],'15.1F5.15-C1.12')
        self.assertEqual(self.dev.facts['version_RE0'],'15.1F5.15-C1.12')
        self.assertEqual(self.dev.facts['version_RE1'],'15.1F5.15')

    @patch('jnpr.junos.Device.execute')
    def test_sw_info_txp(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_txp
        self.assertEqual(self.dev.facts['junos_info']['re0']['text'],
                         '13.3R9-S2.1')
        self.assertEqual(self.dev.facts['hostname'], 'dj')
        self.assertEqual(self.dev.facts['model'],'T1600')
        self.assertEqual(self.dev.facts['model_info'], {'re0': 'T1600'})
        self.assertEqual(self.dev.facts['version'],'13.3R9-S2.1')
        self.assertEqual(self.dev.facts['version_RE0'],'13.3R9-S2.1')
        self.assertEqual(self.dev.facts['version_RE1'],None)

    @patch('jnpr.junos.Device.execute')
    def test_sw_info_ex(self, mock_execute):
        mock_execute.side_effect = self._mock_manager_ex
        self.assertEqual(self.dev.facts['junos_info']['re0']['text'],
                         '11.4R1.6')
        self.assertEqual(self.dev.facts['hostname'], 'sw1')
        self.assertEqual(self.dev.facts['model'],'EX2200-C-12T-2G')
        self.assertEqual(self.dev.facts['model_info'],
                         {'re0': 'EX2200-C-12T-2G'})
        self.assertEqual(self.dev.facts['version'],'11.4R1.6')
        self.assertEqual(self.dev.facts['version_RE0'],'11.4R1.6')
        self.assertEqual(self.dev.facts['version_RE1'],None)

    @patch('jnpr.junos.Device.execute')
    def test_sw_info_nfx(self, mock_execute):
        self.dev.facts._cache['vc_capable']=False
        mock_execute.side_effect = self._mock_manager_nfx
        self.assertEqual(self.dev.facts['hostname'], 'jdm')
        self.assertEqual(self.dev.facts['model'],'NFX250_S2_10_T')
        self.assertEqual(self.dev.facts['version'],'15.1X53-D45.3')
        self.assertEqual(self.dev.facts['version_RE0'],'15.1X53-D45.3')
        self.assertEqual(self.dev.facts['version_RE1'],None)
        self.assertEqual(self.dev.facts['model_info'],
                         {'re0': 'NFX250_S2_10_T'})
        self.assertEqual(self.dev.facts['junos_info']['re0']['text'],
                         '15.1X53-D45.3')

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(foo,
                              self.dev._conn._device_handler
                              .transform_reply())._NCElement__doc[0]
        return rpc_reply

    def _mock_manager_setup(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

    def _mock_manager_single(self, *args, **kwargs):
        if args:
            return self._read_file('sw_info_single_' + args[0].tag +
                                   '.xml')

    def _mock_manager_vc(self, *args, **kwargs):
        if args:
            if (args[0].tag == 'command' and
               args[0].text == 'show version invoke-on all-routing-engines'):
                raise RpcError()
            else:
                return self._read_file('sw_info_vc_' + args[0].tag + '.xml')


    def _mock_manager_simple(self, *args, **kwargs):
        if args:
            if (args[0].tag == 'command'):
                raise RpcError()
            else:
                return self._read_file('sw_info_simple_' + args[0].tag + '.xml')

    def _mock_manager_no_version(self, *args, **kwargs):
        if args:
            if (args[0].tag == 'command'):
                raise RpcError()
            else:
                return self._read_file('sw_info_no_version_' + args[0].tag +
                                       '.xml')

    def _mock_manager_dual(self, *args, **kwargs):
        if args:
            return self._read_file('sw_info_dual_' + args[0].tag + '.xml')

    def _mock_manager_txp(self, *args, **kwargs):
        if args:
            if (args[0].tag == 'command'):
                raise RpcError()
            else:
                return self._read_file('sw_info_txp_' + args[0].tag + '.xml')

    def _mock_manager_ex(self, *args, **kwargs):
        if args:
            if (args[0].tag == 'command'):
                raise RpcError()
            else:
                return self._read_file('sw_info_ex_' + args[0].tag + '.xml')

    def _mock_manager_nfx(self, *args, **kwargs):
        if args:
            if (args[0].tag == 'command'):
                raise RpcError()
            elif (args[0].tag == 'get-software-information' and
                  args[0].find('./*') is None):
                return True
            else:
                return self._read_file('sw_info_nfx_' + args[0].tag + '.xml')
