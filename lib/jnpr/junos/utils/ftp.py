"""
FTP utility
"""

import re
import ftplib


class FTP:
    """
    FTP utility can be used to transfer files to and from device.
    """

    def __init__(self, junos, **ftpargs):
        """

        :param Device junos: Device object
        :param kvargs ftpargs: any additional args to be passed to ftplib FTP

        Supports python *context-manager* pattern.  For example::

            from jnpr.junos.utils.ftp import FTP
            with FTP(dev) as dev_ftp:
                dev_ftp.retrbinary('RETR ' + "/var/home/regress/file1",
                                    open("file1", 'wb').write)
                dev_ftp.storbinary('STOR ' + "/var/home/regress/file11",
                                    open("file11", 'rb'))
        """

        self._junos = junos
        self._ftpargs = ftpargs

    def open(self, **ftpargs):
        """
        Creates an instance of the FTP object and returns to caller for use.

        .. note:: This method uses the same username/password authentication
                   credentials as used by :class:`jnpr.junos.device.Device`.

        :returns: ftplib.FTP object
        """
        if not self._junos.facts.get('hostname', None):
            raise RuntimeError('Could not hostname of the device')

        if 'user' not in ftpargs:
            ftpargs['user'] = self._junos._auth_user
        if 'passwd' not in ftpargs:
            ftpargs['passwd'] = self._junos._auth_password

        self._ftp = ftplib.FTP(self._junos.facts['hostname'])
        self._ftp.login(**ftpargs)

        return self._ftp

    def upload_file(self, local_file, remote_file=None):
        """
        This function is used to upload file to the router from local
        execution server/shell.

        :param local_file: Full path along with filename which has to be
            copied to router
        :param remote_file: Full path along with filename to which the FILE
            has to be copied the router. If ignored FILE will be copied to "tmp"
        :returns: True if the transfer succeeds, else False

        """

        try:
            if not remote_file:
                mat = re.search('^.*/(.*)$', local_file)
                if mat:
                    remote_file = '/tmp/' + mat.group(1)
                else:
                    remote_file = '/tmp/' + local_file
            self._ftp.storbinary('STOR ' + remote_file, open(local_file, 'rb'))
        except Exception as exp:
            return False
        return True

    def dnload_file(self, local_file, remote_file):
        """
        This function is used to download file from router to local execution
        server/shell.

        :param local_file: Full path along with filename to which the FILE has
            to be copied

        :param remote_file: Full path along with filename on the router. If
            ignored FILE will be copied to "tmp"

        :returns: True if the transfer succeeds, else False
        """

        try:
            self._ftp.retrbinary('RETR ' + remote_file,
                                 open(local_file, 'wb').write)
        except Exception as exp:
            return False
        return True

    def close(self):
        """
        Closes the FTP connection to the device
        """
        self._ftp.close()

    # -------------------------------------------------------------------------
    # CONTEXT MANAGER
    # -------------------------------------------------------------------------

    def __enter__(self):
        return self.open(**self._ftpargs)

    def __exit__(self, exc_ty, exc_val, exc_tb):
        return self.close()
