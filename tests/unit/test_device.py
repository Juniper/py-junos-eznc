'''

@author: rsherman
'''
import unittest
from mock import MagicMock, patch
import os

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession

from jnpr.junos.facts.swver import version_info

facts = {'domain': None, 'hostname': 'firefly', 'ifd_style': 'CLASSIC',
          'version_info': version_info('12.1X46-D15.3'),
          '2RE': False, 'serialnumber': 'aaf5fe5f9b88', 'fqdn': 'firefly',
          'virtual': True, 'switch_style': 'NONE', 'version': '12.1X46-D15.3',
          'HOME': '/cf/var/home/rick', 'srx_cluster': False,
          'model': 'FIREFLY-PERIMETER',
          'RE0': {'status': 'Testing',
                    'last_reboot_reason': 'Router rebooted after a '
                                        'normal shutdown.',
                    'model': 'FIREFLY-PERIMETER RE',
                    'up_time': '6 hours, 29 minutes, 30 seconds'},
          'vc_capable': False, 'personality': 'SRX_BRANCH'}

class TestDevice(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self.mock_manager
        from jnpr.junos import Device
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()

    @patch('ncclient.operations.session.CloseSession.request')
    def tearDown(self, mock_session):
        self.dev.close()

    def test_device_property_logfile_isinstance(self):
        mock = MagicMock()
        with patch('__builtin__.open', mock):
            with patch('__builtin__.file', MagicMock):
                handle = open('filename', 'r')
                self.dev.logfile = handle
                self.assertEqual(self.dev.logfile, handle)

    def test_device_property_logfile_close(self):
        self.dev._logfile = MagicMock()
        self.dev._logfile.close.return_value = 0
        self.dev.logfile = None
        self.assertFalse(self.dev._logfile)

    def test_device_open(self):
        self.assertEqual(self.dev.connected, True)

    @patch('jnpr.junos.Device.execute')
    def test_device_facts(self, mock_execute):
        mock_execute.side_effect = self.mock_manager
        self.dev.facts_refresh()
        assert self.dev.facts['version'] == facts['version']

    def test_device_hostname(self):
        assert self.dev.hostname == '1.1.1.1'

    def test_device_user(self):
        assert self.dev.user == 'rick'

    def test_device_get_password(self):
        assert self.dev.password is None

    def test_device_set_password(self):
        self.dev.password = 'secret'
        assert self.dev._password == 'secret'

    def test_device_get_timeout(self):
        assert self.dev.timeout == 30

    def test_device_set_timeout(self):
        self.dev.timeout = 10
        assert self.dev.timeout == 10

    def test_device_cli(self):
        self.dev.execute = MagicMock(name='execute')
        self.dev.cli('show version')
        assert self.dev.execute.call_args[0][0].text == 'show version'

    def test_device_cli_exception(self):
        self.dev.rpc.cli = MagicMock(side_effect=AttributeError)
        val = self.dev.cli('show version')
        self.assertEqual(val, 'invalid command: show version')

    def test_device_execute(self):
        self.dev.execute = MagicMock(name='execute')
        self.dev.execute('<get-software-information/>')
        self.assertEqual(self.dev.execute.call_args[0][
            0], '<get-software-information/>')

    def test_device_rpcmeta(self):
        assert self.dev.rpc.get_software_information.func_doc ==\
            'get-software-information'

    def test_device_probe_timeout_zero(self):
        with patch('jnpr.junos.device.socket') as mock_socket:
            self.assertFalse(self.dev.probe(0))

    def test_device_probe_timeout_gt_zero(self):
        with patch('jnpr.junos.device.socket') as mock_socket:
            self.assertTrue(self.dev.probe(1),
                            'probe fn is not working for'
                            ' timeout greater than zero')

    def test_device_probe_timeout_exception(self):
        with patch('jnpr.junos.device.socket') as mock_socket:
            with patch('jnpr.junos.device.time.sleep') as mock_time:
                mock_socket.socket.return_value.close.side_effect \
                    = RuntimeError
                mock_time.return_value = None
                self.assertFalse(self.dev.probe(.01))

    def test_device_bind(self):
        self.dev.bind()
        mock = MagicMock()
        mock.__name__ = 'magic mock'
        self.dev.bind(kw=mock)

    def test_device_template(self):
        self.dev._j2ldr = MagicMock()
        self.dev.Template('test')

    def test_device_close(self):
        def close_conn():
            self.dev.connected = False
        self.dev.close = MagicMock(name='close')
        self.dev.close.side_effect = close_conn
        self.dev.close()
        self.assertEqual(self.dev.connected, False)


    def read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__), fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(foo, self.dev._conn._device_handler.transform_reply())._NCElement__doc[0]
        return rpc_reply

 
    def mock_manager(self, *args, **kwargs):
        from jnpr.junos.exception import RpcError
        if kwargs:
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        elif args:
            if args[0].tag == 'command':
                if args[0].text == 'show cli directory':
                    return self.read_file('show-cli-directory.xml')
                else:
                    raise RpcError

            else:
                return self.read_file(args[0].tag + '.xml')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'TestDevice.testName']
    unittest.main()
