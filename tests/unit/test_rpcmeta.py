__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
import os
from nose.plugins.attrib import attr

from jnpr.junos.device import Device
from jnpr.junos.rpcmeta import _RpcMetaExec
from jnpr.junos.facts.swver import version_info
from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession

from mock import patch, MagicMock, call
from lxml import etree


@attr('unit')
class Test_RpcMetaExec(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()
        self.rpc = _RpcMetaExec(self.dev)

    def test_rpcmeta_constructor(self):
        self.assertTrue(isinstance(self.rpc._junos, Device))

    @patch('jnpr.junos.device.Device.execute')
    def test_rpcmeta_load_config(self, mock_execute_fn):
        root = etree.XML('<root><a>test</a></root>')
        self.rpc.load_config(root)
        self.assertEqual(mock_execute_fn.call_args[0][0].tag,
                         'load-configuration')

    @patch('jnpr.junos.device.Device.execute')
    def test_rpcmeta_load_config_with_configuration_tag(self, mock_execute_fn):
        root = etree.XML(
            '<configuration><root><a>test</a></root></configuration>')
        self.rpc.load_config(root)
        self.assertEqual(mock_execute_fn.call_args[0][0].tag,
                         'load-configuration')

    @patch('jnpr.junos.device.Device.execute')
    def test_rpcmeta_load_config_option_action(self, mock_execute_fn):
        set_commands = """
            set system host-name test_rpc
            set system domain-name test.juniper.net
        """
        self.rpc.load_config(set_commands, action='set')
        self.assertEqual(mock_execute_fn.call_args[0][0].get('action'),
                         'set')

    @patch('jnpr.junos.device.Device.execute')
    def test_rpcmeta_option_format(self, mock_execute_fn):
        set_commands = """
            set system host-name test_rpc
            set system domain-name test.juniper.net
        """
        self.rpc.load_config(set_commands, format='text')
        self.assertEqual(mock_execute_fn.call_args[0][0].get('format'),
                         'text')

    @patch('jnpr.junos.device.Device.execute')
    def test_rpcmeta_exec_rpc_vargs(self, mock_execute_fn):
        self.rpc.system_users_information(dict(format='text'))
        self.assertEqual(mock_execute_fn.call_args[0][0].get('format'),
                         'text')

    @patch('jnpr.junos.device.Device.execute')
    def test_rpcmeta_exec_rpc_kvargs(self, mock_execute_fn):
        self.rpc.system_users_information(set_data=('test',))
        self.assertEqual(mock_execute_fn.call_args[0][0][0].text,
                         'test')

    @patch('jnpr.junos.device.Device.execute')
    def test_rpcmeta_exec_rpc_normalize(self, mock_execute_fn):
        self.rpc.any_ole_rpc(normalize=True)
        self.assertEqual(mock_execute_fn.call_args[1], {'normalize': True})

    @patch('jnpr.junos.device.Device.execute')
    def test_rpcmeta_get_config(self, mock_execute_fn):
        root = etree.XML('<root><a>test</a></root>')
        self.rpc.get_config(root)
        self.assertEqual(mock_execute_fn.call_args[0][0].tag,
                         'get-configuration')

    def test_rpcmeta_exec_rpc_format_json_14_2(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.dev._facts['version_info'] = version_info('14.2X46-D15.3')
        op = self.rpc.get_system_users_information(dict(format='json'))
        self.assertEqual(op['system-users-information'][0]
                         ['uptime-information'][0]['date-time'][0]['data'],
                         u'4:43AM')

    def test_rpcmeta_exec_rpc_format_json_gt_14_2(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.dev._facts['version_info'] = version_info('15.1X46-D15.3')
        op = self.rpc.get_system_users_information(dict(format='json'))
        self.assertEqual(op['system-users-information'][0]
                         ['uptime-information'][0]['date-time'][0]['data'],
                         u'4:43AM')

    @patch('jnpr.junos.device.warnings')
    def test_rpcmeta_exec_rpc_format_json_lt_14_2(self, mock_warn):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.dev._facts['version_info'] = version_info('13.1X46-D15.3')
        self.rpc.get_system_users_information(dict(format='json'))
        mock_warn.assert_has_calls(call.warn(
            'Native JSON support is only from 14.2 onwards', RuntimeWarning))

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

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        with open(fpath) as fp:
            foo = fp.read()
        if fname == 'get-system-users-information.xml':
            return NCElement(foo,
                             self.dev._conn._device_handler.transform_reply())
        rpc_reply = NCElement(foo, self.dev._conn.
                              _device_handler.transform_reply())\
            ._NCElement__doc[0]
        return rpc_reply
