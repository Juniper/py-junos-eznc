from __future__ import absolute_import

import paramiko
from scp import SCPClient


class SCP(object):

    def __init__(self, junos, **scpargs):
        """
        constructor that wraps a paramiko 'scp' object.
        """
        self._junos = junos
        self._scpargs = scpargs

    def open(self, **scpargs):
        """
        creates an instance of the scp object and return to caller for use
        """
        #@@@ should check for multi-calls to connect to ensure we don't keep
        #@@@ opening new connections
        junos = self._junos
        self._ssh = paramiko.SSHClient()
        self._ssh.load_system_host_keys()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # use junos._hostname since this will be correct if we are going
        # through a jumphost.

        self._ssh.connect(hostname=junos._hostname,
                          port=(
                              22, int(
                                  junos._port))[
                              junos._hostname == 'localhost'],
                          username=junos._auth_user,
                          password=junos._auth_password,
                          )
        return SCPClient(self._ssh.get_transport(), **scpargs)

    def close(self):
        """
        closes the ssh/scp connection to the device
        """
        self._ssh.close()

    # -------------------------------------------------------------------------
    # CONTEXT MANAGER
    # -------------------------------------------------------------------------

    def __enter__(self):
        return self.open(**self._scpargs)

    def __exit__(self, exc_ty, exc_val, exc_tb):
        self.close()
