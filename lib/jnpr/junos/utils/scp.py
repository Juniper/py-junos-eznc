from __future__ import absolute_import
import inspect

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

        with SCP(dev, progress=True) as scp:
            scp.put(package, remote_path)

    """
    def __init__(self, junos, **scpargs):
        """
        Constructor that wraps :py:mod:`paramiko` and :py:mod:`scp` related objects.

        :param Device junos: the Device object
        :param kvargs scpargs: any additional args to be passed to paramiko SCP
        """
        self._junos = junos
        if self._junos.__dict__.get('_mode') is not None:
            raise RuntimeError('SCP is not supported with Console mode')
        self._scpargs = scpargs
        self._by10pct = 0
        self._user_progress = self._scpargs.get('progress')
        if self._user_progress is True:
            self._scpargs['progress'] = self._scp_progress
        elif callable(self._user_progress):
            # User case also define progress with 3 params, the way scp module
            # expects. Function will take path, total size, transferred.
            # https://github.com/jbardin/scp.py/blob/master/scp.py#L97
            spec = inspect.getargspec(self._user_progress)
            if len(spec.args) == 3:
                self._scpargs['progress'] = self._user_progress
            else:
                # this will override the function _progress defined for this
                # class to use progress provided by user.
                self._progress = lambda report: \
                    self._user_progress(self._junos, report)
                self._scpargs['progress'] = self._scp_progress

    def _progress(self, report):
        """ simple progress report function """
        print (self._junos.hostname + ": " + report)

    def _scp_progress(self, _path, _total, _xfrd):

        # calculate current percentage xferd
        pct = int(float(_xfrd) / float(_total) * 100)

        # if 10% more has been copied, then print a message
        if 0 == (pct % 10) and pct != self._by10pct:
            self._by10pct = pct
            self._progress(
                "%s: %s / %s (%s%%)" %
                (_path, _xfrd, _total, str(pct)))

    def open(self, **scpargs):
        """
        Creates an instance of the scp object and return to caller for use.

        .. note:: This method uses the same username/password authentication
                   credentials as used by :class:`jnpr.junos.device.Device`.
                   It can also use ``ssh_private_key_file`` option if provided
                   to the :class:`jnpr.junos.device.Device` 

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

        config = {}
        kwargs = {}
        ssh_config = getattr(junos, '_sshconf_path')
        if ssh_config:
            config = paramiko.SSHConfig()
            config.parse(open(ssh_config))
            config = config.lookup(junos._hostname)
        sock = None
        if config.get("proxycommand"):
            sock = paramiko.proxy.ProxyCommand(config.get("proxycommand"))

        if self._junos._ssh_private_key_file is not None:
            kwargs['key_filename']=self._junos._ssh_private_key_file

        self._ssh.connect(hostname=junos._hostname,
                          port=(
                              22, int(
                                  junos._port))[
                              junos._hostname == 'localhost'],
                          username=junos._auth_user,
                          password=junos._auth_password,
                          sock=sock, **kwargs
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
