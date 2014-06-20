from __future__ import absolute_import

import paramiko
from scp import SCPClient

"""
Secure Copy Utility
"""


class SCP(object):
    """
    The SCP utility is used to conjunction with :class:`jnpr.junos.utils.sw.SW`
    when transferring the Junos image to the device.  The :class:`SCP` can be
    used for other secure-copy use-cases as well; it is implemented to support
    the python *context-manager* pattern.  For example::

        from jnpr.junos.utils.scp import SCP

        with SCP( dev, progress=_scp_progress ) as scp:
            scp.put( package, remote_path )

    """
    def __init__(self, junos, **scpargs):
        """
        Constructor that wraps :py:mod:`paramiko` and :py:mod:`scp` related objects.

        :param Device junos: the Device object
        :param kvargs scpargs: any additional args to be passed to paramiko SCP
        """
        self._junos = junos
        self._scpargs = scpargs

    def open(self, **scpargs):
        """
        Creates an instance of the scp object and return to caller for use.

        .. note:: This method uses the same username/password authentication
                   credentials as used by :class:`jnpr.junos.device.Device`.

        .. warning:: The :class:`jnpr.junos.device.Device` ``ssh_private_key_file``
                     option is currently **not** supported.

        .. todo:: add support for ``ssh_private_key_file``.

        :returns: SCPClient object
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
        Closes the ssh/scp connection to the device
        """
        self._ssh.close()

    # -------------------------------------------------------------------------
    # CONTEXT MANAGER
    # -------------------------------------------------------------------------

    def __enter__(self):
        return self.open(**self._scpargs)

    def __exit__(self, exc_ty, exc_val, exc_tb):
        self.close()
