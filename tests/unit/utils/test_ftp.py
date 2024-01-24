import unittest
import nose2
import ftplib
import sys
import os

from jnpr.junos import Device
import jnpr.junos.utils.ftp

from mock import patch

if sys.version < "3":
    builtin_string = "__builtin__"
else:
    builtin_string = "builtins"


@unittest.skipIf(sys.platform == "win32", "will work for windows in coming days")
class TestFtp(unittest.TestCase):
    @patch("ftplib.FTP.connect")
    @patch("ftplib.FTP.login")
    @patch("ftplib.FTP.close")
    @patch("ncclient.manager.connect")
    def setUp(self, mock_connect, mock_ftp_connect, mock_ftpconnect, mock_ftplogin):
        self.dev = Device(
            host="1.1.1.1", user="testuser", passwd="testpasswd", gather_facts=False
        )
        self.dev.open()
        self.dev._facts = {"hostname": "1.1.1.1"}
        self.dev_ftp = jnpr.junos.utils.ftp.FTP(self.dev)

    def test_ftp_open(self):
        assert isinstance(self.dev_ftp, ftplib.FTP)

    @patch("ftplib.FTP.login")
    @patch("ftplib.FTP.connect")
    def test_ftp_open_erors(self, mock_ftpconnect, mock_ftplogin):
        jnpr.junos.utils.ftp.FTP(self.dev)
        mock_ftplogin.assert_called_with("testuser", "testpasswd", "")

    #

    @patch("ftplib.FTP.close")
    def test_ftp_close(self, mock_close):
        self.dev_ftp.open()
        self.dev_ftp.close()
        mock_close.assert_called()

    @patch("ftplib.FTP.connect")
    @patch("ftplib.FTP.login")
    @patch("ftplib.FTP.close")
    def test_ftp_context(self, mock_ftpconnect, mock_ftplogin, mock_ftpclose):
        with jnpr.junos.utils.ftp.FTP(self.dev) as dev_ftp:
            assert isinstance(dev_ftp, ftplib.FTP)

    @patch(builtin_string + ".open")
    def test_ftp_upload_file_errors(self, mock_open):
        self.assertEqual(self.dev_ftp.put(local_file="testfile"), False)
        self.assertEqual(self.dev_ftp.put(local_file="/var/testfile"), False)

    @patch("ftplib.FTP.storbinary")
    @patch(builtin_string + ".open")
    def test_ftp_upload_file(self, mock_ftpstore, mock_open):
        self.assertEqual(self.dev_ftp.put(local_file="testfile"), True)

    @patch(builtin_string + ".open")
    def test_ftp_dnload_file_errors(self, mock_open):
        self.assertEqual(
            self.dev_ftp.get(local_path="testfile", remote_file="testfile"), False
        )

    @patch(builtin_string + ".open")
    def test_ftp_dnload_file_get(self, mock_open):
        self.assertEqual(self.dev_ftp.get(remote_file="/var/tmp/testfile"), False)

    @patch("ftplib.FTP.retrbinary")
    @patch(builtin_string + ".open")
    def test_ftp_dnload_file_get_retr(self, mock_open, mock_ftpretr):
        self.assertEqual(self.dev_ftp.get(remote_file="/var/tmp/testfile"), True)

    @patch("ftplib.FTP.retrbinary")
    @patch(builtin_string + ".open")
    def test_ftp_dnload_file_get_rf_filename(self, mock_open, mock_ftpretr):
        self.assertEqual(self.dev_ftp.get(remote_file="testfile.txt"), True)

    @patch("ftplib.FTP.retrbinary")
    @patch(builtin_string + ".open")
    def test_ftp_dnload_file(self, mock_ftpretr, mock_open):
        self.assertEqual(
            self.dev_ftp.get(local_path="testfile", remote_file="testfile"), True
        )

    @patch("ftplib.FTP.connect")
    @patch("ftplib.FTP.login")
    @patch("ftplib.FTP.retrbinary")
    def test_ftp_dnload_file_get_rf_filename_cb(
        self,
        mock_ftp_connect,
        mock_ftp_login,
        mock_ftp_retrbinary,
    ):
        def callback():
            pass

        kwargs = {"callback": callback}
        dev_ftp = jnpr.junos.utils.ftp.FTP(self.dev, **kwargs)
        self.assertEqual(dev_ftp.get(remote_file="/var/tmp/testfile"), True)

    @patch("ftplib.FTP.storbinary")
    @patch(builtin_string + ".open")
    def test_ftp_upload_file_rem_path(self, mock_open, mock_ftpstore):
        self.assertEqual(
            self.dev_ftp.put(local_file="/var/tmp/conf.txt", remote_path="/var/tmp"),
            True,
        )
        self.assertEqual(
            tuple(mock_ftpstore.call_args)[1]["cmd"], "STOR /var/tmp/conf.txt"
        )

    @patch("ftplib.FTP.storbinary")
    @patch(builtin_string + ".open")
    def test_ftp_upload_file_rem_full_path(self, mock_open, mock_ftpstore):
        self.assertEqual(
            self.dev_ftp.put(
                local_file=os.path.abspath("/var/tmp/conf.txt"),
                remote_path=os.path.abspath("/var/tmp/test.txt"),
            ),
            True,
        )
        self.assertEqual(
            tuple(mock_ftpstore.call_args)[1]["cmd"],
            "STOR " + os.path.abspath("/var/tmp/test.txt"),
        )

    @patch("ftplib.FTP.storbinary")
    @patch(builtin_string + ".open")
    def test_ftp_upload_file_rem_path_create(self, mock_open, mock_ftpstore):
        self.assertEqual(
            self.dev_ftp.put(
                local_file="conf.txt", remote_path=os.path.abspath("/var/tmp")
            ),
            True,
        )
        self.assertEqual(
            tuple(mock_ftpstore.call_args)[1]["cmd"],
            "STOR " + os.path.abspath("/var/tmp/conf.txt"),
        )
