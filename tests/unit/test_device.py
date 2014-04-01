'''

@author: rsherman
'''
import unittest
import mock
from mock import MagicMock, patch, PropertyMock, sentinel

from jnpr.junos import Device

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession

facts = {'domain': None, 'hostname': 'firefly', 'ifd_style': 'CLASSIC',
         'version_info': 'junos.version_info(major=(12, 1), type=X,'
                         ' minor=(46, \'D\', 10), build=2)',
         '2RE': False, 'serialnumber': '123456789102', 'fqdn': 'firefly',
         'virtual': True, 'switch_style': 'NONE', 'version': '12.1X46-D10.2',
         'HOME': '/cf/var/home/rick', 'srx_cluster': False,
         'model': 'FIREFLY-PERIMETER',
         'RE0': {'status': 'Testing',
                 'last_reboot_reason': 'Router rebooted after a '
                                       'normal shutdown.',
                 'model': 'FIREFLY-PERIMETER RE',
                 'up_time': '1 minute, 10 seconds'},
         'personality': 'SRX_BRANCH'}


class TestDevice(unittest.TestCase):

    def setUp(self):
        self.dev = Device(host='1.1.1.1', user='rick', password='password123')
        self.dev.connected = True
        self.dev._facts = facts
        self.device_params = {'name': 'junos'}

        self.device_handler = make_device_handler(self.device_params)

        self.session = SSHSession(self.device_handler)
        self.dev._conn = Manager(self.session, self.device_handler)

    def tearDown(self):
        self.session._connected = False

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

    @patch.object(Device, 'facts_refresh')
    def test_device_open(self, mock_facts_refresh):
        with patch('jnpr.junos.device.netconf_ssh') as mock_netconf_ssh:
            self.dev.open()
            self.assertEqual(self.dev.connected, True)

    def test_device_facts(self):
        assert self.dev.facts == facts

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
        self.dev.execute = mock.MagicMock(name='execute')
        self.dev.cli('show version')
        assert self.dev.execute.call_args[0][0].text == 'show version'

    def test_device_cli_exception(self):
        self.dev.rpc.cli = MagicMock(side_effect=AttributeError)
        val = self.dev.cli('show version')
        self.assertEqual(val, 'invalid command: show version')

    def test_device_execute(self):
        self.dev.execute = mock.MagicMock(name='execute')
        self.dev.execute('<get-software-information/>')
        assert self.dev.execute.call_args[0][
            0] == '<get-software-information/>'

    def test_device_rpcmeta(self):
        assert self.dev.rpc.get_software_information.func_doc == \
            'get-software-information'

    def test_device_close(self):
        self.dev._conn = mock.MagicMock(name='close')
        self.dev.close()
        self.assertEqual(self.dev.connected, False)

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
