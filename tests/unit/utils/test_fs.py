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
        self.fs._dev.rpc.set_cli_working_directory(directory='test/report')

    def test_pwd(self):
        self.fs.dev._conn.rpc = MagicMock(side_effect=self._mock_manager)
        self.fs.pwd()


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
                                  .transform_reply())._NCElement__doc
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




    # @patch('paramiko.SSHClient')
    # def test_scp_open(self, mock_connect):
    #     from scp import SCPClient
    #     self.dev.bind(scp=SCP)
    #     assert isinstance(self.dev.scp.open(), SCPClient)
    #
    # @patch('paramiko.SSHClient')
    # def test_scp_close(self, mock_connect):
    #     self.dev.bind(scp=SCP)
    #     self.dev.scp.open()
    #     self.assertIsNone(self.dev.scp.close())
    #
    # @patch('paramiko.SSHClient')
    # def test_scp_context(self, mock_connect):
    #     with SCP(self.dev) as scp:
    #         scp.get('addrbook.conf')
