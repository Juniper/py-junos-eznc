
import unittest
from nose.plugins.attrib import attr
import ftplib
import sys

from jnpr.junos import Device
import jnpr.junos.utils.ftp

from mock import patch

if sys.version < '3':
    builtin_string = '__builtin__'
else:
    builtin_string = 'builtins'


@attr('unit')
class TestFtp(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        self.dev = Device(host='1.1.1.1', user="testuser",
                          passwd="testpasswd",
                          gather_facts=False)
        self.dev.open()
        self.dev._facts = {'hostname': '1.1.1.1'}

    @patch('ftplib.FTP.connect')
    @patch('ftplib.FTP.login')
    def test_ftp_open(self, mock_Ftpconnect, mock_ftplogin):
        dev_ftp = jnpr.junos.utils.ftp.FTP(self.dev)
        assert isinstance(dev_ftp, ftplib.FTP)

    @patch('ncclient.manager.connect')
    @patch('ftplib.FTP.connect')
    def test_ftp_open_erors(self, mock_connect, mock_ftpconnect):
        dev2 = Device(host='1.1.1.1', user="testuser",
                      passwd="testpasswd",
                      gather_facts=False)
        dev2.open()
        dev_ftp = jnpr.junos.utils.ftp.FTP(dev2)
        self.assertRaises(Exception, dev_ftp.open)

    @patch('ftplib.FTP.connect')
    @patch('ftplib.FTP.login')
    @patch('ftplib.FTP.close')
    def test_ftp_close(self, mock_close, mock_ftplogin, mock_connect):
        dev_ftp = jnpr.junos.utils.ftp.FTP(self.dev)
        dev_ftp.open()
        dev_ftp.close()
        mock_close.assert_called()

    @patch('ftplib.FTP.connect')
    @patch('ftplib.FTP.login')
    @patch('ftplib.FTP.close')
    def test_ftp_context(self, mock_ftpconnect, mock_ftplogin, mock_ftpclose):
        with jnpr.junos.utils.ftp.FTP(self.dev) as dev_ftp:
            assert isinstance(dev_ftp, ftplib.FTP)

    @patch('ftplib.FTP.connect')
    @patch('ftplib.FTP.login')
    @patch('ftplib.FTP.close')
    @patch(builtin_string + '.open')
    def test_ftp_upload_file_errors(self, mock_ftpconnect, mock_ftplogin,
                                    mock_ftpclose, mock_open):
        dev_ftp = jnpr.junos.utils.ftp.FTP(self.dev)
        dev_ftp.open()
        self.assertEqual(dev_ftp.put(local_file="testfile"), False)
        self.assertEqual(dev_ftp.put(local_file="/var/testfile"),
                         False)

    @patch('ftplib.FTP.connect')
    @patch('ftplib.FTP.login')
    @patch('ftplib.FTP.close')
    @patch('ftplib.FTP.storbinary')
    @patch(builtin_string + '.open')
    def test_ftp_upload_file(self, mock_ftpconnect, mock_ftplogin,
                             mock_ftpclose, mock_ftpstore, mock_open):
        dev_ftp = jnpr.junos.utils.ftp.FTP(self.dev)
        dev_ftp.open()
        self.assertEqual(dev_ftp.put(local_file="testfile"), True)

    @patch('ftplib.FTP.connect')
    @patch('ftplib.FTP.login')
    @patch('ftplib.FTP.close')
    @patch(builtin_string + '.open')
    def test_ftp_dnload_file_errors(self, mock_ftpconnect, mock_ftplogin,
                                    mock_ftpclose, mock_open):
        dev_ftp = jnpr.junos.utils.ftp.FTP(self.dev)
        dev_ftp.open()
        self.assertEqual(dev_ftp.get(local_path="testfile",
                                             remote_file="testfile"), False)

    @patch('ftplib.FTP.connect')
    @patch('ftplib.FTP.login')
    @patch('ftplib.FTP.close')
    @patch('ftplib.FTP.retrbinary')
    @patch(builtin_string + '.open')
    def test_ftp_dnload_file(self, mock_ftpconnect, mock_ftplogin,
                             mock_ftpclose, mock_ftpretr, mock_open):
        dev_ftp = jnpr.junos.utils.ftp.FTP(self.dev)
        dev_ftp.open()
        self.assertEqual(dev_ftp.get(local_path="testfile",
                                             remote_file="testfile"), True)
