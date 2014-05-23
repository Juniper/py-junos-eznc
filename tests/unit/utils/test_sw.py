__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr

import os
import sys
from cStringIO import StringIO
from contextlib import contextmanager

from jnpr.junos import Device
from jnpr.junos.exception import RpcError
from jnpr.junos.utils.sw import SW
from jnpr.junos.facts.swver import version_info
from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession

from jnpr.junos.exception import RpcError
from lxml import etree

from mock import patch, MagicMock, call, mock_open


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
class TestSW(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()
        self.dev._facts = facts
        self.sw = self.get_sw()

    @patch('jnpr.junos.Device.execute')
    def get_sw(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        return SW(self.dev)

    @patch('ncclient.operations.session.CloseSession.request')
    def tearDown(self, mock_session):
        self.dev.close()

    def test_sw_hashfile(self):
        with patch('__builtin__.open', mock_open(), create=True) as m:
            import jnpr.junos.utils.sw
            with open('foo') as h:
                h.read.side_effect = ('abc', 'a', '')
                jnpr.junos.utils.sw._hashfile(h, MagicMock())
                self.assertEqual(h.read.call_count, 3)

    @patch('jnpr.junos.Device.execute')
    def test_sw_constructor_multi_re(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw = SW(self.dev)
        self.assertFalse(self.sw._multi_RE)

    @patch('jnpr.junos.Device.execute')
    def test_sw_constructor_multi_vc(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw = SW(self.dev)
        self.assertFalse(self.sw._multi_VC)

    @patch('__builtin__.open')
    def test_sw_local_sha256(self, mock_built_open):
        package = 'test.tgz'
        self.assertEqual(SW.local_sha256(package),
                         'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934'
                         'ca495991b7852b855')

    @patch('__builtin__.open')
    def test_sw_local_md5(self, mock_built_open):
        package = 'test.tgz'
        self.assertEqual(SW.local_md5(package),
                         'd41d8cd98f00b204e9800998ecf8427e')

    @patch('__builtin__.open')
    def test_sw_local_sha1(self, mock_built_open):
        package = 'test.tgz'
        self.assertEqual(SW.local_sha1(package),
                         'da39a3ee5e6b4b0d3255bfef95601890afd80709')

    def test_sw_progress(self):
        with self.capture(SW.progress, self.dev, 'running') as output:
            self.assertEqual('1.1.1.1: running\n', output)

    @patch('paramiko.SSHClient')
    @patch('scp.SCPClient.put')
    def test_sw_put(self, mock_scp_put, mock_scp):
        #mock_scp_put.side_effect = self.mock_put
        package = 'test.tgz'
        self.sw.put(package)
        self.assertTrue(call('test.tgz', '/var/tmp') in mock_scp_put.mock_calls)

    @patch('jnpr.junos.utils.scp.SCP.__exit__')
    @patch('jnpr.junos.utils.scp.SCP.__init__')
    @patch('jnpr.junos.utils.scp.SCP.__enter__')
    def test_sw_put_progress(self, mock_enter, mock_scp, mock_exit):
        package = 'test.tgz'
        mock_scp.side_effect = self._fake_scp
        self.sw.put(package, progress=self._myprogress)
        self.assertEqual(mock_scp.call_args_list[0][1]['progress'].by10pct, 50)

    def _fake_scp(self, *args, **kwargs):
        progress = kwargs['progress']
        progress('test.tgz', 100, 50)

    @patch('jnpr.junos.Device.execute')
    def test_sw_pkgadd(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'test.tgz'
        self.assertTrue(self.sw.pkgadd(package))

    @patch('jnpr.junos.Device.execute')
    def test_sw_validate(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'package.tgz'
        self.assertTrue(self.sw.validate(package))

    @patch('jnpr.junos.Device.execute')
    def test_sw_safe_copy(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'safecopy.tgz'
        self.sw.put = MagicMock()
        SW.local_md5 = MagicMock()

        self.assertTrue(self.sw.safe_copy(package, progress=self._myprogress, cleanfs=True,
                                          checksum='96a35ab371e1ca10408c3caecdbd8a67'))

    @patch('jnpr.junos.Device.execute')
    def test_sw_safe_copy_return_false(self, mock_execute):
        # not passing checksum value, will get random from magicmock
        mock_execute.side_effect = self._mock_manager
        package = 'safecopy.tgz'
        self.sw.put = MagicMock()
        SW.local_md5 = MagicMock()

        self.assertFalse(self.sw.safe_copy(package, progress=self._myprogress,
                                           cleanfs=True))
        SW.local_md5.assert_called_with(package)

    @patch('jnpr.junos.Device.execute')
    def test_sw_safe_copy_checksum_none(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'safecopy.tgz'
        self.sw.put = MagicMock()
        SW.local_md5 = MagicMock(return_value='96a35ab371e1ca10408c3caecdbd8a67')

        self.assertTrue(self.sw.safe_copy(package, progress=self._myprogress,
                                          cleanfs=True))

    @patch('jnpr.junos.Device.execute')
    def test_sw_safe_install(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'install.tgz'
        self.sw.put = MagicMock()
        SW.local_md5 = MagicMock(return_value='96a35ab371e1ca10408c3caecdbd8a67')
        self.assertTrue(self.sw.install(package, progress=self._myprogress,
                                        cleanfs=True))

    @patch('jnpr.junos.utils.sw.SW.safe_copy')
    def test_sw_safe_install_copy_fail(self, mock_copy):
        mock_copy.return_value = False
        self.assertFalse(self.sw.install('file'))

    @patch('jnpr.junos.utils.sw.SW.validate')
    def test_sw_install_validate(self, mock_validate):
        mock_validate.return_value = False
        self.assertFalse(self.sw.install('file', validate=True, no_copy=True))

    @patch('jnpr.junos.utils.sw.SW.pkgadd')
    def test_sw_install_multi_mx(self, mock_pkgadd):
        mock_pkgadd.return_value = True
        self.sw._multi_RE = True
        self.sw._multi_MX = True
        self.assertTrue(self.sw.install('file', no_copy=True))

    @patch('jnpr.junos.utils.sw.SW.pkgadd')
    def test_sw_install_multi_vc(self, mock_pkgadd):
        mock_pkgadd.return_value = True
        self.sw._multi_RE = True
        self.sw._multi_VC = True
        self.sw._RE_list = ('version_RE0', 'version_RE1')
        self.assertTrue(self.sw.install('file', no_copy=True))

    @patch('jnpr.junos.Device.execute')
    def test_sw_rollback(self, mock_execute):
        # we need proper xml for this test case, update request-package-roll
        # back.xml
        mock_execute.side_effect = self._mock_manager
        self.assertEqual(self.sw.rollback(), '')

    def test_sw_inventory(self):
        self.sw.dev.rpc.file_list = \
            MagicMock(side_effect=self._mock_manager)
        self.assertEqual(self.sw.inventory,
                             {'current': None, 'rollback': None})

    @patch('jnpr.junos.Device.execute')
    def test_sw_reboot(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw._multi_MX = True
        self.assertTrue('Shutdown NOW' in self.sw.reboot())

    @patch('jnpr.junos.Device.execute')
    def test_sw_reboot_exception(self, mock_execute):
        rsp = etree.XML('<rpc-reply><a>test</a></rpc-reply>')
        mock_execute.side_effect = RpcError(rsp=rsp)
        self.assertRaises(Exception, self.sw.reboot)

    @patch('jnpr.junos.Device.execute')
    def test_sw_poweroff(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw._multi_MX = True
        self.assertTrue('Shutdown NOW' in self.sw.poweroff())

    @patch('jnpr.junos.Device.execute')
    def test_sw_poweroff_exception(self, mock_execute):
        rsp = etree.XML('<rpc-reply><a>test</a></rpc-reply>')
        mock_execute.side_effect = RpcError(rsp=rsp)
        self.assertRaises(Exception, self.sw.poweroff)

    def _myprogress(self, dev, report):
        pass

    @contextmanager
    def capture(self, command, *args, **kwargs):
        out, sys.stdout = sys.stdout, StringIO()
        command(*args, **kwargs)
        sys.stdout.seek(0)
        yield sys.stdout.read()
        sys.stdout = out

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()
        rpc_reply = NCElement(foo, self.dev._conn._device_handler.transform_reply())._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            if 'path' in kwargs:
                if kwargs['path'] == '/packages':
                    return self._read_file('file-list_dir.xml')
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        elif args:
            return self._read_file(args[0].tag + '.xml')
