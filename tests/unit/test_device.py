'''

@author: rsherman
'''
import unittest
import mock
import os

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
        self.device_params = {'name': 'junos'}
        self.device_handler = make_device_handler(self.device_params)
        self.session = SSHSession(self.device_handler)

        from jnpr.junos import Device
        self.dev = Device(host='1.1.1.1', user='rick', password='password123')

    def tearDown(self):
        self.session._connected = False

    @mock.patch('ncclient.manager.connect')
    @mock.patch('jnpr.junos.Device.execute')
    def test_device_open(self, mock_connect, mock_execute):
        mock_connect.side_effect = self.mock_manager
        mock_execute.side_effect = self.mock_manager
        self.dev.open()
        self.assertEqual(self.dev.connected, True)

#     def test_device_facts(self):
#         print self.dev.facts
#         assert self.dev.facts == facts

    def test_device_hostname(self):
        assert self.dev.hostname == '1.1.1.1'

    def test_device_user(self):
        assert self.dev.user == 'rick'

    def test_device_get_password(self):
        assert self.dev.password is None

    def test_device_set_password(self):
        self.dev.password = 'secret'
        assert self.dev._password == 'secret'

#     def test_device_get_timeout(self):
#         assert self.dev.timeout == 30

#     def test_device_set_timeout(self):
#         self.dev.timeout = 10
#         assert self.dev.timeout == 10

#     def test_device_cli(self):
#         print self.dev.cli('show cli directory', format='xml')
#         assert self.dev.cli('show cli directory').findtext('./working-directory') == '/cf/var/home/rick</working-directory'

#     def test_device_execute(self):
#         self.dev.execute = mock.MagicMock(name='execute')
#         self.dev.execute('<get-software-information/>')
#         self.assertEqual(self.dev.execute.call_args[0][
#             0], '<get-software-information/>')
# 
#     def test_device_rpcmeta(self):
#         assert self.dev.rpc.get_software_information.func_doc ==\
#             'get-software-information'

    def test_device_close(self):
        def close_conn():
            self.dev.connected = False
        self.dev.close = mock.MagicMock(name='close')
        self.dev.close.side_effect = close_conn
        self.dev.close()
        self.assertEqual(self.dev.connected, False)


    def read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__), fname)
        foo = open(fpath).read()

        rpc_reply = NCElement(foo, self.device_handler.transform_reply())._NCElement__doc[0]
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
