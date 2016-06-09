
import unittest
from nose.plugins.attrib import attr
from ftplib import FTP
import sys

from jnpr.junos import Device
from jnpr.junos.utils.ftp import Ftp

from mock import patch

if sys.version<'3':
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
        dev_ftp = Ftp(self.dev)
        assert isinstance(dev_ftp.open(), FTP)

    @patch('ncclient.manager.connect')
    @patch('ftplib.FTP.connect')
    def test_ftp_open_erors(self, mock_connect, mock_ftpconnect):
        dev2 = Device(host='1.1.1.1', user="testuser",
                      passwd="testpasswd",
                      gather_facts=False)
        dev2.open()
        dev_ftp = Ftp(dev2)
        self.assertRaises(Exception, dev_ftp.open)

    @patch('ftplib.FTP.connect')
    @patch('ftplib.FTP.login')
    @patch('ftplib.FTP.close')
    def test_ftp_close(self, mock_Ftpconnect, mock_ftplogin, mock_ftpclose):
        dev_ftp = Ftp(self.dev)
        dev_ftp.open()
        self.assertEqual(dev_ftp.close(), None)

    @patch('ftplib.FTP.connect')
    @patch('ftplib.FTP.login')
    @patch('ftplib.FTP.close')
    def test_ftp_context(self, mock_ftpconnect, mock_ftplogin, mock_ftpclose):
        with Ftp(self.dev) as dev_ftp:
            assert isinstance(dev_ftp, FTP)

    @patch('ftplib.FTP.connect')
    @patch('ftplib.FTP.login')
    @patch('ftplib.FTP.close')
    @patch(builtin_string + '.open')
    def test_ftp_upload_file_errors(self, mock_ftpconnect, mock_ftplogin,
                                    mock_ftpclose, mock_open):
        dev_ftp = Ftp(self.dev)
        dev_ftp.open()
        self.assertEqual(dev_ftp.upload_file(local_file="testfile"), False)
        self.assertEqual(dev_ftp.upload_file(local_file="/var/testfile"),
                         False)

    @patch('ftplib.FTP.connect')
    @patch('ftplib.FTP.login')
    @patch('ftplib.FTP.close')
    @patch('ftplib.FTP.storbinary')
    @patch(builtin_string + '.open')
    def test_ftp_upload_file(self, mock_ftpconnect, mock_ftplogin,
                             mock_ftpclose, mock_ftpstore, mock_open):
        dev_ftp = Ftp(self.dev)
        dev_ftp.open()
        self.assertEqual(dev_ftp.upload_file(local_file="testfile"), True)

    @patch('ftplib.FTP.connect')
    @patch('ftplib.FTP.login')
    @patch('ftplib.FTP.close')
    @patch(builtin_string + '.open')
    def test_ftp_dnload_file_errors(self, mock_ftpconnect, mock_ftplogin,
                                    mock_ftpclose, mock_open):
        dev_ftp = Ftp(self.dev)
        dev_ftp.open()
        self.assertEqual(dev_ftp.dnload_file(local_file="testfile",
                                             remote_file="testfile"), False)

    @patch('ftplib.FTP.connect')
    @patch('ftplib.FTP.login')
    @patch('ftplib.FTP.close')
    @patch('ftplib.FTP.retrbinary')
    @patch(builtin_string + '.open')
    def test_ftp_dnload_file(self, mock_ftpconnect, mock_ftplogin,
                             mock_ftpclose, mock_ftpretr, mock_open):
        dev_ftp = Ftp(self.dev)
        dev_ftp.open()
        self.assertEqual(dev_ftp.dnload_file(local_file="testfile",
                                             remote_file="testfile"), True)
