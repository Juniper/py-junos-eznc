from __future__ import absolute_import
import inspect

from scp import SCPClient
from jnpr.junos.utils.ssh_client import open_ssh_client

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
        Constructor that wraps :py:mod:`paramiko` and :py:mod:`scp` objects.

        :param Device junos: the Device object
        :param kvargs scpargs: any additional args to be passed to paramiko SCP
        """
        self._junos = junos
        if self._junos.__dict__.get("_mode") is not None:
            raise RuntimeError("SCP is not supported with Console mode")
        self._scpargs = scpargs
        self._by10pct = 0
        self._user_progress = self._scpargs.get("progress")
        self._ssh = None
        if self._user_progress is True:
            self._scpargs["progress"] = self._scp_progress
        elif callable(self._user_progress):
            # User case also define progress with 3 params, the way scp module
            # expects. Function will take path, total size, transferred.
            # https://github.com/jbardin/scp.py/blob/master/scp.py#L97
            spec = inspect.getargspec(self._user_progress)
            if (len(spec.args) == 3 and spec.args[0] != "self") or (
                len(spec.args) == 4 and spec.args[0] == "self"
            ):
                self._scpargs["progress"] = self._user_progress
            else:
                # this will override the function _progress defined for this
                # class to use progress provided by user.
                self._progress = lambda report: self._user_progress(self._junos, report)
                self._scpargs["progress"] = self._scp_progress

    def _progress(self, report):
        """ simple progress report function """
        print(self._junos.hostname + ": " + report)

    def _scp_progress(self, _path, _total, _xfrd):

        # calculate current percentage xferd
        pct = int(float(_xfrd) / float(_total) * 100)

        # if 10% more has been copied, then print a message
        if 0 == (pct % 10) and pct != self._by10pct:
            self._by10pct = pct
            self._progress("%s: %s / %s (%s%%)" % (_path, _xfrd, _total, str(pct)))

    def open(self, **scpargs):
        """
        Creates an instance of the scp object and return to caller for use.

        .. note:: This method uses the same username/password authentication
                   credentials as used by :class:`jnpr.junos.device.Device`.
                   It can also use ``ssh_private_key_file`` option if provided
                   to the :class:`jnpr.junos.device.Device`

        :returns: SCPClient object
        """
        # @@@ should check for multi-calls to connect to ensure we don't keep
        # @@@ opening new connections
        self._ssh = open_ssh_client(dev=self._junos)
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
