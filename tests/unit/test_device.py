'''

@author: rsherman
'''
import unittest
import mock

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
         'RE0': {
             'status': 'Testing',
             'last_reboot_reason': 'Router rebooted after a normal shutdown.',
             'model': 'FIREFLY-PERIMETER RE', 'up_time': '1 minute,'
                                                         ' 10 seconds'},
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

    def test_device_open(self):
        self.dev.open = mock.MagicMock(name='open')
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

    def test_device_execute(self):
        self.dev.execute = mock.MagicMock(name='execute')
        self.dev.execute('<get-software-information/>')
        self.assertEqual(self.dev.execute.call_args[0][
            0], '<get-software-information/>')

    def test_device_rpcmeta(self):
        assert self.dev.rpc.get_software_information.func_doc ==\
            'get-software-information'

    def test_device_close(self):
        def close_conn():
            self.dev.connected = False
        self.dev.close = mock.MagicMock(name='close')
        self.dev.close.side_effect = close_conn
        self.dev.close()
        self.assertEqual(self.dev.connected, False)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'TestDevice.testName']
    unittest.main()
