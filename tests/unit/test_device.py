'''

@author: rsherman
'''
import unittest
from nose.plugins.attrib import attr
from mock import MagicMock, patch, mock_open
import os
from lxml.builder import E
from lxml import etree

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession

from jnpr.junos.facts.swver import version_info
from jnpr.junos import Device
from jnpr.junos.exception import RpcError

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


@attr('unit')
class Test_MyTemplateLoader(unittest.TestCase):
    def setUp(self):
        from jnpr.junos.device import _MyTemplateLoader
        self.template_loader = _MyTemplateLoader()

    @patch('__builtin__.filter')
    def test_temp_load_get_source_filter_false(self, filter_mock):
        filter_mock.return_value = False
        try:
            self.template_loader.get_source(None, None)
        except Exception as ex:
            import jinja2
            self.assertEqual(type(ex), jinja2.exceptions.TemplateNotFound)

    @patch('jnpr.junos.device.os.path')
    def test_temp_load_get_source_filter_true(self, os_path_mock):
        #cant use @patch here as with statement will have exit
        m = mock_open()
        with patch('__builtin__.file', m, create=True):
            self.template_loader.get_source(None, None)


@attr('unit')
class TestDevice(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
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

    def test_device_host_mand_param(self):
        self.assertRaises(ValueError, Device, user='rick',
                          password='password123',
                          gather_facts=False)

    def test_device_property_logfile_close(self):
        self.dev._logfile = MagicMock()
        self.dev._logfile.close.return_value = 0
        self.dev.logfile = None
        self.assertFalse(self.dev._logfile)

    def test_device_property_logfile_exception(self):
        try:
            self.dev.logfile = True
        except Exception as ex:
            self.assertEqual(type(ex), ValueError)

    def test_device_repr(self):
        localdev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.assertEqual(repr(localdev), 'Device(1.1.1.1)')

    @patch('jnpr.junos.device.os')
    @patch('__builtin__.open')
    def test_device__sshconf_lkup(self, os_mock, open_mock):
        os_mock.path.exists.return_value = True
        self.dev._sshconf_lkup()

    @patch('ncclient.manager.connect')
    @patch('jnpr.junos.Device.execute')
    def test_device_open(self, mock_connect, mock_execute):
        with patch('jnpr.junos.utils.fs.FS.cat') as mock_cat:        
            mock_cat.return_value = """

    domain jls.net

            """          
            mock_connect.side_effect = self._mock_manager
            mock_execute.side_effect = self._mock_manager
            self.dev2 = Device(host='2.2.2.2', user='rick', password='password123')
            self.dev2.open()
            self.assertEqual(self.dev2.connected, True)

    @patch('jnpr.junos.Device.execute')
    def test_device_facts(self, mock_execute):          
        with patch('jnpr.junos.utils.fs.FS.cat') as mock_cat:
            mock_execute.side_effect = self._mock_manager
            mock_cat.return_value = """

    domain jls.net

            """          
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

    def test_device_manages(self):
        self.assertEqual(self.dev.manages, [],
                         'By default manages will be empty list')

    def test_device_set_facts_exception(self):
        try:
            self.dev.facts = 'test'
        except RuntimeError as ex:
            self.assertEqual(RuntimeError, type(ex))

    def test_device_cli(self):
        self.dev.execute = MagicMock(name='execute')
        self.dev.cli('show version')
        assert self.dev.execute.call_args[0][0].text == 'show version'

    def test_device_cli_exception(self):
        self.dev.rpc.cli = MagicMock(side_effect=AttributeError)
        val = self.dev.cli('show version')
        self.assertEqual(val, 'invalid command: show version')

    def test_device_execute(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.dev.execute('<get-system-core-dumps/>')

    def test_device_execute_topy(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.dev.execute('<get-system-core-dumps/>', to_py=self._do_nothing)

    def test_device_execute_exception(self):
        class MyException(Exception):
            rpc_err = """
<rpc-error xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:junos="http://xml.juniper.net/junos/12.1X46/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
<error-severity>error</error-severity>
<error-info>
<bad-element>get-bgp-summary-information</bad-element>
</error-info>
<error-message>permission denied</error-message>
</rpc-error>                
            """
            xml = etree.XML(rpc_err)

        self.dev._conn.rpc = MagicMock(side_effect=MyException)
        self.assertRaises(RpcError, self.dev.execute, 
            '<get-software-information/>')

    def test_device_execute_rpc_error(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.assertRaises(RpcError, self.dev.rpc.get_rpc_error)

    def test_device_execute_index_error(self):
        self.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.assertTrue(self.dev.rpc.get_index_error())

    def test_device_execute_ValueError(self):
        self.assertRaises(ValueError, self.dev.execute, None)

    def test_device_rpcmeta(self):
        assert self.dev.rpc.get_software_information.func_doc ==\
            'get-software-information'

    def test_device_probe_timeout_zero(self):
        with patch('jnpr.junos.device.socket'):
            self.assertFalse(self.dev.probe(0))

    def test_device_probe_timeout_gt_zero(self):
        with patch('jnpr.junos.device.socket'):
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
        #for *args
        self.dev.bind(mock)
        #for **kwargs
        self.dev.bind(kw=mock)

    def test_device_bind_varg_exception(self):
        with self.assertRaises(ValueError):
            self.dev.bind()
            mock = MagicMock()
            mock.__name__ = 'magic mock'
            #for *args
            self.dev.bind(mock)
            self.dev.bind(mock)

    def test_device_bind_kvarg_exception(self):
        with self.assertRaises(ValueError):
            self.dev.bind()
            mock = MagicMock()
            mock.__name__ = 'magic mock'
            #for **kwargs
            self.dev.bind(kw=mock)
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

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()

        if (fname == 'get-rpc-error.xml' or
                fname == 'get-index-error.xml' or
                fname == 'get-system-core-dumps.xml'):
            rpc_reply = NCElement(foo, self.dev._conn._device_handler
                                  .transform_reply())
        else:
            rpc_reply = NCElement(foo, self.dev._conn._device_handler
                                  .transform_reply())._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        elif args:
            if args[0].tag == 'command':
                if args[0].text == 'show cli directory':
                    return self._read_file('show-cli-directory.xml')
                else:
                    raise RpcError

            else:
                return self._read_file(args[0].tag + '.xml')

    def _do_nothing(self, *args, **kwargs):
        return

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'TestDevice.testName']
    unittest.main()
