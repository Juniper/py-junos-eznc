__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr
import os

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession

from jnpr.junos import Device
from jnpr.junos.utils.fs import FS

from mock import patch, MagicMock


@attr('unit')
class TestFS(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()
        self.fs = FS(self.dev)

    def test_cat_wrong_path_return_none(self):
        path = 'test/report'
        self.assertIsNone(self.fs.cat(path))

    def test_cat(self):
        self.fs._dev.rpc.file_show = MagicMock()
        path = 'test/report'
        self.fs.cat(path)
        self.fs._dev.rpc.file_show.assert_called_with(filename='test/report')

    def test_cwd(self):
        self.fs._dev.rpc.set_cli_working_directory = MagicMock()
        folder = 'test/report'
        self.fs.cwd(folder)
        self.fs._dev.rpc.set_cli_working_directory.\
            assert_called_with(directory='test/report')

    @patch('jnpr.junos.Device.execute')
    def test_pwd(self, mock_execute):
        mock_execute.side_effect = MagicMock(side_effect=self._mock_manager)
        self.fs.pwd()
        self.assertEqual(self.fs.pwd(), '/cf/var/home/rick')

    # def test_pwd(self):
    #     self.fs.dev.rpc = MagicMock(side_effect=self._mock_manager)
    #     self.fs.pwd()

    def test_checksum_return_none(self):
        path = 'test/report'
        self.assertIsNone(self.fs.checksum(path))

    def test_checksum_unknown_calc(self):
        path = 'test/report'
        self.assertRaises(ValueError, self.fs.checksum, path=path, calc='abc')

    def test_checksum_return_rsp(self):
        self.fs.dev.rpc.get_sha256_checksum_information = \
            MagicMock(side_effect=self._mock_manager)
        path = 'test/checksum'
        self.assertEqual(self.fs.checksum(path, 'sha256'), 'xxxx')
        self.fs.dev.rpc.get_sha256_checksum_information.\
            assert_called_with(path='test/checksum')

    def test_stat_calling___decode_file(self):
        path = 'test/stat/decode_file'
        self.fs.dev.rpc.file_list = \
            MagicMock(side_effect=self._mock_manager)
        self.assertDictEqual(self.fs.stat(path),
                             {'owner': 'pqr', 'path': '/var/abc.sh',
                              'permissions': 755,
                              'permissions_text': '-rwxr-xr-x', 'size': 2,
                              'ts_date': 'Mar 13 06:54',
                              'ts_epoc': '1394693680',
                              'type': 'file'})

    def test_stat_calling___decode_dir(self):
        path = 'test/stat/decode_dir'
        self.fs.dev.rpc.file_list = \
            MagicMock(side_effect=self._mock_manager)
        self.assertDictEqual(self.fs.stat(path),
                         {'path': '/var', 'type': 'dir', 'file_count': 1,
                          'size': 2})

    def test_stat_return_none(self):
        path = 'test/abc'
        self.fs.dev.rpc.file_list = MagicMock()
        self.fs.dev.rpc.file_list.find.return_value = 'output'
        self.assertIsNone(self.fs.stat(path))

    def test_ls_calling___decode_file(self):
        path = 'test/stat/decode_file'
        self.fs.dev.rpc.file_list = \
            MagicMock(side_effect=self._mock_manager)
        self.assertDictEqual(self.fs.ls(path),
                             {'owner': 'pqr', 'path': '/var/abc.sh',
                              'permissions': 755,
                              'permissions_text': '-rwxr-xr-x', 'size': 2,
                              'ts_date': 'Mar 13 06:54',
                              'ts_epoc': '1394693680',
                              'type': 'file'})

    def test_ls_calling___decode_dir(self):
        path = 'test/stat/decode_dir'
        self.fs.dev.rpc.file_list = \
            MagicMock(side_effect=self._mock_manager)
        self.assertDictEqual(self.fs.ls(path),
                         {'files':
                              {'abc': {'permissions_text': 'drwxr-xr-x',
                                       'ts_date': 'Feb 17 15:30',
                                       'ts_epoc': '1392651039',
                                       'owner': 'root', 'path': 'abc',
                                       'size': 2, 'type': 'dir',
                                       'permissions': 555}},
                          'path': '/var', 'type': 'dir', 'file_count': 1,
                          'size': 2})

    def test_ls_return_none(self):
        path = 'test/abc'
        self.fs.dev.rpc.file_list = MagicMock()
        self.fs.dev.rpc.file_list.find.return_value = 'output'
        self.assertIsNone(self.fs.ls(path))

    def test_rm(self):
        self.fs.dev.rpc.file_delete = MagicMock(return_value=True)
        path = 'test/abc'
        self.assertTrue(self.fs.rm(path))
        self.fs.dev.rpc.file_delete.assert_called_once_with(
            path = 'test/abc')
        self.fs.dev.rpc.file_delete = MagicMock(return_value=False)
        self.assertFalse(self.fs.rm(path))

    def test_copy(self):
        self.fs.dev.rpc.file_copy = MagicMock()
        initial = 'test/abc'
        final = 'test/xyz'
        self.assertTrue(self.fs.cp(initial, final))
        self.fs.dev.rpc.file_copy.assert_called_once_with(
            source='test/abc',
            destination='test/xyz')
        self.fs.dev.rpc.file_copy = MagicMock(side_effect=Exception)
        self.assertFalse(self.fs.cp(initial, final))

    def test_move(self):
        self.fs.dev.rpc.file_rename = MagicMock(return_value=True)
        initial = 'test/abc'
        final = 'test/xyz'
        self.assertTrue(self.fs.mv(initial, final))
        self.fs.dev.rpc.file_rename.assert_called_once_with(
            source='test/abc',
            destination='test/xyz')
        self.fs.dev.rpc.file_rename = MagicMock(return_value=False)
        self.assertFalse(self.fs.mv(initial, final))

    @patch('jnpr.junos.Device.execute')
    def test_storage_usage(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertDictEqual(self.fs.storage_usage(),
                             {'/dev/abc':
                                  {'avail_block': 234234,
                                   'used_blocks': 2346455, 'used_pct': '1',
                                   'mount': '/', 'total_blocks': 567431,
                                   'avail': '2F', 'used': '481M',
                                   'total': '4F'}})


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
        elif (fname == 'show-configuration.xml' or
              fname == 'show-system-alarms.xml'):
            rpc_reply = NCElement(foo, self.dev._conn._device_handler
                                  .transform_reply())._NCElement__doc
        else:
            rpc_reply = NCElement(foo, self.dev._conn._device_handler
                                  .transform_reply())._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            # if 'path' in kwargs and 'detail' in kwargs:
            #     return self._read_file('dir_list_detail.xml')

            if 'path' in kwargs:
                if kwargs['path']=='test/stat/decode_dir':
                    return self._read_file('file-list_dir.xml')
                elif kwargs['path']=='test/stat/decode_file':
                    return self._read_file('file-list_file.xml')
                elif kwargs['path']=='test/checksum':
                    return self._read_file('checksum.xml')
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)


        elif args:
            if args[0].tag == 'command':
                if args[0].text == 'show cli directory':
                    return self._read_file('show-cli-directory.xml')
            elif args[0].tag == 'get-system-storage':
                return self._read_file('get-system-storage.xml')



