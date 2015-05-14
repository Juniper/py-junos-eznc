__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr
import os

from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession

from jnpr.junos import Device
from jnpr.junos.utils.fs import FS

from mock import patch, MagicMock, call


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
        self.assertEqual(self.fs.cat(path), None)

    def test_cat(self):
        self.fs._dev.rpc.file_show = MagicMock(side_effect=self._mock_manager)
        path = 'test/cat.txt'
        self.assertTrue('testing cat functionality' in self.fs.cat(path))
        self.fs._dev.rpc.file_show.assert_called_with(filename='test/cat.txt')

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

    def test_checksum_return_none(self):
        path = 'test/report'
        self.assertEqual(self.fs.checksum(path), None)

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
        self.assertEqual(self.fs.stat(path),
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
        self.assertEqual(self.fs.stat(path),
                         {'path': '/var', 'type': 'dir', 'file_count': 1,
                          'size': 2})

    def test_stat_return_none(self):
        path = 'test/abc'
        self.fs.dev.rpc.file_list = MagicMock()
        self.fs.dev.rpc.file_list.find.return_value = 'output'
        self.assertEqual(self.fs.stat(path), None)

    def test_ls_calling___decode_file(self):
        path = 'test/stat/decode_file'
        self.fs.dev.rpc.file_list = \
            MagicMock(side_effect=self._mock_manager)
        self.assertEqual(self.fs.ls(path),
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
        self.assertEqual(self.fs.ls(path),
                         {'files':
                          {'abc': {'permissions_text': 'drwxr-xr-x',
                                   'ts_date': 'Feb 17 15:30',
                                   'ts_epoc': '1392651039',
                                   'owner': 'root', 'path': 'abc',
                                   'size': 2, 'type': 'dir',
                                   'permissions': 555}},
                          'path': '/var', 'type': 'dir',
                          'file_count': 1,
                          'size': 2})

    def test_ls_return_none(self):
        path = 'test/abc'
        self.fs.dev.rpc.file_list = MagicMock()
        self.fs.dev.rpc.file_list.find.return_value = 'output'
        self.assertEqual(self.fs.ls(path), None)

    @patch('jnpr.junos.utils.fs.FS._decode_file')
    def test_ls_link_path_false(self, mock_decode_file):
        mock_decode_file.get.return_value = False
        path = 'test/stat/decode_file'
        self.fs.dev.rpc.file_list = \
            MagicMock(side_effect=self._mock_manager)
        self.fs.ls(path, followlink=False)
        mock_decode_file.assert_has_calls(call().get('link'))

    def test_ls_brief_true(self):
        path = 'test/stat/decode_dir'
        self.fs.dev.rpc.file_list = \
            MagicMock(side_effect=self._mock_manager)
        self.assertEqual(self.fs.ls(path, brief=True),
                         {'files': ['abc'], 'path': '/var',
                          'type': 'dir', 'file_count': 1, 'size': 2})

    def test_ls_calling___decode_dir_type_symbolic_link(self):
        path = 'test/stat/decode_symbolic_link'
        self.fs.dev.rpc.file_list = \
            MagicMock(side_effect=self._mock_manager)
        self.assertEqual(self.fs.ls(path),
                         {'files':
                          {'abc': {'permissions_text': 'drwxr-xr-x',
                                   'ts_date': 'Feb 17 15:30',
                                   'link': 'symlink test',
                                   'ts_epoc': '1392651039',
                                   'owner': 'root', 'path': 'abc',
                                   'size': 2, 'type': 'link',
                                   'permissions': 555}},
                          'path': '/var', 'type': 'dir', 'file_count': 1,
                          'size': 2})

    def test_rm_return_true(self):
        self.fs.dev.rpc.file_delete = MagicMock(return_value=True)
        path = 'test/abc'
        self.assertTrue(self.fs.rm(path))
        self.fs.dev.rpc.file_delete.assert_called_once_with(
            path='test/abc')

    def test_rm_return_false(self):
        path = 'test/abc'
        self.fs.dev.rpc.file_delete = MagicMock(return_value=False)
        self.assertFalse(self.fs.rm(path))
        self.fs.dev.rpc.file_delete.assert_called_once_with(
            path='test/abc')

    def test_copy_return_true(self):
        self.fs.dev.rpc.file_copy = MagicMock()
        initial = 'test/abc'
        final = 'test/xyz'
        self.assertTrue(self.fs.cp(initial, final))
        self.fs.dev.rpc.file_copy.assert_called_once_with(
            source='test/abc',
            destination='test/xyz')

    def test_copy_return_false(self):
        initial = 'test/abc'
        final = 'test/xyz'
        self.fs.dev.rpc.file_copy = MagicMock(side_effect=Exception)
        self.assertFalse(self.fs.cp(initial, final))
        self.fs.dev.rpc.file_copy.assert_called_once_with(
            source='test/abc',
            destination='test/xyz')

    def test_move_return_true(self):
        self.fs.dev.rpc.file_rename = MagicMock(return_value=True)
        initial = 'test/abc'
        final = 'test/xyz'
        self.assertTrue(self.fs.mv(initial, final))
        self.fs.dev.rpc.file_rename.assert_called_once_with(
            source='test/abc',
            destination='test/xyz')

    def test_move_return_false(self):
        initial = 'test/abc'
        final = 'test/xyz'
        self.fs.dev.rpc.file_rename = MagicMock(return_value=False)
        self.assertFalse(self.fs.mv(initial, final))
        self.fs.dev.rpc.file_rename.assert_called_once_with(
            source='test/abc',
            destination='test/xyz')

    def test_tgz_return_true(self):
        src = 'test/tgz.txt'
        dst = 'test/xyz'
        self.fs.dev.rpc.file_archive = MagicMock(return_value=True)
        self.assertTrue(self.fs.tgz(src, dst))
        self.fs.dev.rpc.file_archive.assert_called_once_with(
            source='test/tgz.txt',
            destination='test/xyz', compress=True)

    @patch('jnpr.junos.Device.execute')
    def test_tgz_return_error(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        src = 'test/tgz.txt'
        dst = 'test/xyz'
        self.assertTrue('testing tgz' in self.fs.tgz(src, dst))

    @patch('jnpr.junos.utils.fs.StartShell')
    def test_rmdir(self, mock_StartShell):
        path = 'test/rmdir'
        print(self.fs.rmdir(path))
        calls = [
            call().__enter__(),
            call().__enter__().run('rmdir test/rmdir'),
            call().__exit__(None, None, None)]
        mock_StartShell.assert_has_calls(calls)

    @patch('jnpr.junos.utils.fs.StartShell')
    def test_mkdir(self, mock_StartShell):
        path = 'test/mkdir'
        print(self.fs.mkdir(path))
        calls = [
            call().__enter__(),
            call().__enter__().run('mkdir -p test/mkdir'),
            call().__exit__(None, None, None)]
        mock_StartShell.assert_has_calls(calls)

    @patch('jnpr.junos.utils.fs.StartShell')
    def test_symlink(self, mock_StartShell):
        src = 'test/tgz.txt'
        dst = 'test/xyz'
        print(self.fs.symlink(src, dst))
        calls = [
            call().__enter__(),
            call().__enter__().run('ln -sf test/tgz.txt test/xyz'),
            call().__exit__(None, None, None)]
        mock_StartShell.assert_has_calls(calls)

    @patch('jnpr.junos.Device.execute')
    def test_storage_usage(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertEqual(self.fs.storage_usage(),
                         {'/dev/abc':
                          {'avail_block': 234234,
                           'used_blocks': 2346455, 'used_pct': '1',
                           'mount': '/', 'total_blocks': 567431,
                           'avail': '2F', 'used': '481M',
                           'total': '4F'}})

    @patch('jnpr.junos.Device.execute')
    def test_storage_cleanup(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertEqual(self.fs.storage_cleanup(),
                         {'/var/abc.txt':
                          {'ts_date': 'Apr 25 10:38', 'size': 11}})

    @patch('jnpr.junos.Device.execute')
    def test_storage_cleanup_check(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.assertEqual(self.fs.storage_cleanup_check(),
                         {'/var/abc.txt':
                          {'ts_date': 'Apr 25 10:38', 'size': 11}})

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
                if kwargs['path'] == 'test/stat/decode_dir':
                    return self._read_file('file-list_dir.xml')
                elif kwargs['path'] == 'test/stat/decode_file':
                    return self._read_file('file-list_file.xml')
                elif kwargs['path'] == 'test/checksum':
                    return self._read_file('checksum.xml')
                elif kwargs['path'] == 'test/stat/decode_symbolic_link':
                    return self._read_file('file-list_symlink.xml')
            if 'filename' in kwargs:
                if kwargs['filename'] == 'test/cat.txt':
                    return self._read_file('file-show.xml')
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
            elif args[0].tag == 'request-system-storage-cleanup':
                return self._read_file('request-system-storage-cleanup.xml')
            elif args[0].tag == 'file-archive':
                return self._read_file('file-archive.xml')
