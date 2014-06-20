# stdlib
import hashlib
import re
from os import path
import logging

# 3rd-party modules
from lxml.builder import E

# local modules
from jnpr.junos.utils.util import Util
from jnpr.junos.utils.scp import SCP

"""
Software Installation Utilities
"""

__all__ = ['SW']


def _hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.hexdigest()


class SW(Util):
    """
    Software Utility class, used to perform a software upgrade and
    associated functions.  These methods have been tested on
    *simple deployments*.  Refer to **install** for restricted
    use-cases for software upgrades.

    **Primary methods:**
      * :meth:`install`: perform the entire software installation process
      * :meth:`reboot`: reboots the system for the new image to take effect
      * :meth:`poweroff`: shutdown the system

    **Helpers:** (Useful as standalone as well)
      * :meth:`put`: SCP put package file onto Junos device
      * :meth:`pkgadd`: performs the 'request' operation to install the package
      * :meth:`validate`: performs the 'request' to validate the package

    **Miscellaneous:**
      * rollback: same as 'request softare rollback'
      * inventory: (property) provides file info for current and rollback
        images on the device
    """

    def __init__(self, dev):
        Util.__init__(self, dev)
        self._RE_list = [
            x for x in dev.facts.keys() if x.startswith('version_RE')]
        self._multi_RE = bool(len(self._RE_list) > 1)
        self._multi_VC = bool(
            self._multi_RE is True and dev.facts.get('vc_capable') is True)

    # -----------------------------------------------------------------------
    # CLASS METHODS
    # -----------------------------------------------------------------------

    @classmethod
    def local_sha256(cls, package):
        """
        Computes the SHA-256 value on the package file.

        :param str package:
          File-path to the package (\*.tgz) file on the local server

        :returns: SHA-256 checksum (str)
        :raises IOError: when **package** file does not exist
        """
        return _hashfile(open(package, 'rb'), hashlib.sha256())

    @classmethod
    def local_md5(cls, package):
        """
        Computes the MD5 checksum value on the local package file.

        :param str package:
          File-path to the package (\*.tgz) file on the local server

        :returns: MD5 checksum (str)
        :raises IOError: when **package** file does not exist
        """
        return _hashfile(open(package, 'rb'), hashlib.md5())

    @classmethod
    def local_sha1(cls, package):
        """
        computes the SHA1 checksum value on the local package file.

        :param str package:
          File-path to the package (\*.tgz) file on the local server

        :returns: SHA1 checksum (str)
        :raises IOError: when **package** file does not exist
        """
        return _hashfile(open(package, 'rb'), hashlib.sha1())

    @classmethod
    def progress(cls, dev, report):
        """ simple progress report function """
        print dev.hostname + ": " + report

    # -------------------------------------------------------------------------
    # put - SCP put the image onto the device
    # -------------------------------------------------------------------------

    def put(self, package, remote_path='/var/tmp', progress=None):
        """
        SCP 'put' the package file from the local server to the remote device.

        :param str package:
          File path to the package file on the local file system

        :param str remote_path:
          The directory on the device where the package will be copied to.

        :param func progress:
          Callback function to indicate progress.  You can use :meth:`SW.progress`
          for basic reporting.  See that class method for details.
        """
        def _progress(report):
            # report progress only if a progress callback was provided
            if progress is not None:
                progress(self._dev, report)

        def _scp_progress(_path, _total, _xfrd):
            # init static variable
            if not hasattr(_scp_progress, 'by10pct'):
                _scp_progress.by10pct = 0

            # calculate current percentage xferd
            pct = int(float(_xfrd) / float(_total) * 100)

            # if 10% more has been copied, then print a message
            if 0 == (pct % 10) and pct != _scp_progress.by10pct:
                _scp_progress.by10pct = pct
                _progress(
                    "%s: %s / %s (%s%%)" %
                    (_path, _xfrd, _total, str(pct)))

        # check for the logger barncale for 'paramiko.transport'
        plog = logging.getLogger('paramiko.transport')
        if not plog.handlers:
            class NullHandler(logging.Handler):
                def emit(self, record):
                    pass
            plog.addHandler(NullHandler())

        # execute the secure-copy with the Python SCP module
        with SCP(self._dev, progress=_scp_progress) as scp:
            scp.put(package, remote_path)

    # -------------------------------------------------------------------------
    # pkgadd - used to perform the 'request system software add ...'
    # -------------------------------------------------------------------------

    def pkgadd(self, remote_package, **kvargs):
        """
        Issue the 'request system software add' command on the package.
        The "no-validate" options is set by default.  If you want to validate
        the image, do that using the specific :meth:`validate` method.  Also,
        if you want to reboot the device, suggest using the :meth:`reboot` method
        rather ``reboot=True``.

        :param str remote_package:
          The file-path to the install package on the remote (Junos) device.

        :param dict kvargs:
          Any additional parameters to the 'request' command can
          be passed within **kvargs**, following the RPC syntax
          methodology (dash-2-underscore,etc.)

        .. todo:: Add way to notify user why installation failed.
        .. warning:: Refer to the restrictions listed in :meth:`install`.
        """

        args = dict(no_validate=True, package_name=remote_package)
        args.update(kvargs)

        dev_to = self.dev.timeout     # store device/rpc timeout
        # hardset to 1 hr for long running process
        self.dev.timeout = 60 * 60
        rsp = self.rpc.request_package_add(**args)
        self.dev.timeout = dev_to     # restore original timeout

        got = rsp.getparent()
        rc = int(got.findtext('package-result').strip())

        # return True if rc == 0 else got.findtext('output').strip()
        return True if rc == 0 else False

    # -------------------------------------------------------------------------
    # validate - perform 'request' operation to validate the package
    # -------------------------------------------------------------------------

    def validate(self, remote_package):
        """
        Issues the 'request' operation to validate the package against the
        config.

        :returns:
            * ``True`` if validation passes
            * error (str) otherwise
        """
        rsp = self.rpc.request_package_validate(
            package_name=remote_package).getparent()
        errcode = int(rsp.findtext('package-result'))
        return True if 0 == errcode else rsp.findtext('output').strip()

    def remote_checksum(self, remote_package):
        """
        Computes the MD5 checksum on the remote device.

        :param str remote_package:
            The file-path on the remote Junos device

        :returns:
            The MD5 checksum string

        :raises RpcError: when the **remote_package** is not found.

        .. todo:: should trap the error and return ``None`` instead.
        """
        rsp = self.rpc.get_checksum_information(path=remote_package)
        return rsp.findtext('.//checksum').strip()

    # -------------------------------------------------------------------------
    # safe_copy - copies the package and performs checksum
    # -------------------------------------------------------------------------

    def safe_copy(self, package, **kvargs):
        """
        Copy the install package safely to the remote device.  By default
        this means to clean the filesystem to make space, perform the
        secure-copy, and then verify the MD5 checksum.

        :param str package:
            file-path to package on local filesystem
        :param str remote_path:
            file-path to directory on remote device
        :param func progress:
            call-back function for progress updates
        :param bool cleanfs:
            When ``True`` (default) this method will perform the
            "storage cleanup" on the device.
        :param str checksum:
            This is the checksum string as computed on the local system.
            This value will be used to compare the checksum on the
            remote Junos device.

        :returns:
            * ``True`` when the copy was successful
            * ``False`` otherwise
        """
        remote_path = kvargs.get('remote_path', '/var/tmp')
        progress = kvargs.get('progress')
        checksum = kvargs.get('checksum')
        cleanfs = kvargs.get('cleanfs', True)

        def _progress(report):
            if progress is not None:
                progress(self._dev, report)

        if checksum is None:
            _progress('computing local checksum on: %s' % package)
            checksum = SW.local_md5(package)

        if cleanfs is True:
            dto = self.dev.timeout
            self.dev.timeout = 5 * 60
            _progress('cleaning filesystem ...')
            self.rpc.request_system_storage_cleanup()
            self.dev.timeout = dto

        # we want to give the caller an override so we don't always
        # need to copy the file, but the default is to do this, yo!
        self.put(package, remote_path, progress)

        # validate checksum:
        remote_package = remote_path + '/' + path.basename(package)
        _progress('computing remote checksum on: %s' % remote_package)
        remote_checksum = self.remote_checksum(remote_package)

        if remote_checksum != checksum:
            _progress("checksum check failed.")
            return False
        _progress("checksum check passed.")

        return True

    # -------------------------------------------------------------------------
    # install - complete installation process, but not reboot
    # -------------------------------------------------------------------------

    def install(self, package, remote_path='/var/tmp', progress=None,
                validate=False, checksum=None, cleanfs=True, no_copy=False,
                timeout=1800):
        """
        Performs the complete installation of the **package** that includes the
        following steps:

        1. computes the local MD5 checksum if not provided in :checksum:
        2. performs a storage cleanup if :cleanfs: is True
        3. SCP copies the package to the :remote_path: directory
        4. computes remote MD5 checksum and matches it to the local value
        5. validates the package if :validate: is True
        6. installs the package

        .. warning:: This process has been validated on "simple" deployments.

                      Tested:

                      * Single RE devices (EX, QFX, MX, SRX).
                      * MX dual-RE
                      * EX virtual-chassis when all same HW model
                      * QFX virtual-chassis when all same HW model

                      Known Restrictions:

                      * SRX cluster
                      * MX virtual-chassis

        You can get a progress report on this process by providing a **progress**
        callback.

        .. note:: You will need to invoke the :meth:`reboot` method explicitly to reboot
                  the device.

        :param str package:
          The file-path to the install package tarball on the local filesystem

        :param str remote_path:
          The directory on the Junos device where the package file will be
          SCP'd to; the default is ``/var/tmp``.

        :param bool validate:
          When ``True`` this method will perform a config validation against
          the new image

        :param str checksum:
          MD5 hexdigest of the package file. If this is not provided, then this
          method will perform the calculation. If you are planning on using the
          same image for multiple updates, you should consider using the
          :meth:`local_md5` method to pre calculate this value and then provide to
          this method.

        :param bool cleanfs:
          When ``True`` will perform a 'storeage cleanup' before SCP'ing the
          file to the device.  Default is ``True``.

        :param func progress:
          If provided, this is a callback function with a function prototype
          given the Device instance and the report string::

            def myprogress(dev, report):
              print "host: %s, report: %s" % (dev.hostname, report)

        :param int timeout:
          The amount of time (seconds) before declaring an RPC timeout.  This
          argument was added since most of the time the "package add" RPC
          takes a significant amount of time.  The default RPC timeout is
          generally around 30 seconds.  So this :timeout: value will be
          used in the context of the SW installation process.  Defaults to
          30 minutes (30*60=1800)
        """
        def _progress(report):
            if progress is not None:
                progress(self._dev, report)

        dev = self.dev

        # ---------------------------------------------------------------------
        # perform a 'safe-copy' of the image to the remote device
        # ---------------------------------------------------------------------

        if no_copy is False:
            copy_ok = self.safe_copy(package, remote_path=remote_path,
                                     progress=progress, cleanfs=cleanfs,
                                     checksum=checksum)
            if copy_ok is False:
                return False

        # ---------------------------------------------------------------------
        # at this point, the file exists on the remote device
        # ---------------------------------------------------------------------

        remote_package = remote_path + '/' + path.basename(package)

        restore_timeout = dev.timeout      # for restoration later
        dev.timeout = timeout              # set for long timeout

        if validate is True:
            _progress(
                "validating software against current config,"
                " please be patient ...")
            v_ok = self.validate(remote_package)
            if v_ok is not True:
                dev.timeout = restore_timeout
                return v_ok  # will be the string of output

        if self._multi_RE is False:
            # simple case of device with only one RE
            _progress("installing software ... please be patient ...")
            add_ok = self.pkgadd(remote_package)
            dev.timeout = restore_timeout
            return add_ok
        else:
            # we need to update multiple devices
            if self._multi_VC is True:
                ok = True
                # extract the VC number out of the 'version_RE<n>' string
                vc_members = [
                    re.search(
                        '(\d+)',
                        x).group(1) for x in self._RE_list]
                for vc_id in vc_members:
                    _progress(
                        "installing software on VC member: {0} ... please be"
                        " patient ...".format(vc_id))
                    ok &= self.pkgadd(remote_package, member=vc_id)
                dev.timeout = restore_timeout
                return ok
            else:
                # then this is a device with two RE that supports the "re0"
                # and "re1" options to the command (M, MX tested only)
                ok = True
                _progress(
                    "installing software on RE0 ... please be patient ...")
                ok &= self.pkgadd(remote_package, re0=True)
                _progress(
                    "installing software on RE1 ... please be patient ...")
                ok &= self.pkgadd(remote_package, re1=True)
                dev.timeout = restore_timeout
                return ok

    # -------------------------------------------------------------------------
    # rebbot - system reboot
    # -------------------------------------------------------------------------

    def reboot(self, in_min=0):
        """
        Perform a system reboot, with optional delay (in minutes).

        If the device is equipped with dual-RE, then both RE will be
        rebooted.  This code also hanldes EX/QFX VC.

        :param int in_min: time (minutes) before rebooting the device.

        :returns:
            * reboot message (string) if command successful

        :raises RpcError: when command is not successful.

        .. todo:: need to better handle the exception event.
        """
        cmd = E('request-reboot', E('in', str(in_min)))

        if self._multi_RE is True and self._multi_VC is False:
            cmd.append(E('both-routing-engines'))
        try:
            rsp = self.rpc(cmd)
            got = rsp.getparent().findtext('.//request-reboot-status').strip()
            return got
        except Exception as err:
            if err.rsp.findtext('.//error-severity') != 'warning':
                raise err

    # -------------------------------------------------------------------------
    # poweroff - system shutdown
    # -------------------------------------------------------------------------

    def poweroff(self, in_min=0):
        """
        Perform a system shutdown, with optional delay (in minutes) .

        If the device is equipped with dual-RE, then both RE will be
        rebooted.  This code also hanldes EX/QFX VC.

        :param int in_min: time (minutes) before rebooting the device.

        :returns:
            * reboot message (string) if command successful

        :raises RpcError: when command is not successful.

        .. todo:: need to better handle the exception event.
        """
        cmd = E('request-power-off', E('in', str(in_min)))

        if self._multi_RE is True and self._multi_VC is False:
            cmd.append(E('both-routing-engines'))
        try:
            rsp = self.rpc(cmd)
            return rsp.getparent().findtext('.//request-reboot-status').strip()
        except Exception as err:
            if err.rsp.findtext('.//error-severity') != 'warning':
                raise err

    # -------------------------------------------------------------------------
    # rollback - clears the install request
    # -------------------------------------------------------------------------

    def rollback(self):
        """
        issues the 'request' command to do the rollback and returns the string
        output of the results.

        :returns:
            Rollback results (str)
        """
        rsp = self.rpc.request_package_rollback()
        return rsp.text.strip()

    # -------------------------------------------------------------------------
    # inventory - file info on current and rollback packages
    # -------------------------------------------------------------------------

    @property
    def inventory(self):
        """
        Returns dictionary of file listing information for current and rollback
        Junos install packages. This information comes from the /packages
        directory.

        .. warning:: Experimental method; may not work on all platforms.  If
                     you find this not working, please report issue.
        """
        from jnpr.junos.utils.fs import FS
        fs = FS(self.dev)
        pkgs = fs.ls('/packages')
        return dict(current=pkgs['files'].get(
            'junos'), rollback=pkgs['files'].get('junos.old'))
