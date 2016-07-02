"""
FTP utility
"""

import re
import ftplib
import os
import logging

logger = logging.getLogger("jnpr.junos.utils.ftp")


class FTP(ftplib.FTP):
    """
    FTP utility can be used to transfer files to and from device.
    """

    def __init__(self, junos, **ftpargs):
        """

        :param Device junos: Device object
        :param kvargs ftpargs: any additional args to be passed to ftplib FTP

        Supports python *context-manager* pattern.  For example::

            from jnpr.junos.utils.ftp import FTP
            with FTP(dev) as ftp:
                ftp.put(package, remote_path)
        """

        self._junos = junos
        self._ftpargs = ftpargs
        ftplib.FTP.__init__(self, self._junos._hostname, self._junos._auth_user,
                            self._junos._auth_password)

    def put(self, local_file, remote_path=None):
        """
        This function is used to upload file to the router from local
        execution server/shell.

        :param local_file: Full path along with filename which has to be
            copied to router
        :param remote_path: path in which to receive the files on the remote
            host. If ignored FILE will be copied to "tmp"
        :returns: True if the transfer succeeds, else False

        """

        try:
            mat = re.search('^.*/(.*)$', local_file)
            if mat:
                if not remote_path:
                    remote_file = '/tmp/' + mat.group(1)
                else:
                    remote_file = os.path.join(remote_path, mat.group(1))
            else:
                if not remote_path:
                    remote_file = os.path.join('/tmp/', local_file)
                else:
                    remote_file = os.path.join(remote_path, local_file)
            self.storbinary('STOR ' + remote_file, open(local_file, 'rb'))
        except Exception as exp:
            logger.error(exp.message)
            return False
        return True

    def get(self, local_file, remote_file):
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

    # def close(self):
    #     """
    #     Closes the FTP connection to the device
    #     """
    #     self._ftp.close()

    # -------------------------------------------------------------------------
    # CONTEXT MANAGER
    # -------------------------------------------------------------------------

    def __enter__(self):
        # return self.open(**self._ftpargs)
        return self

    def __exit__(self, exc_ty, exc_val, exc_tb):
        return self.close()
