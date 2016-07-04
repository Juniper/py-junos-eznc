# stdlib
import hashlib
import re
from os import path
import sys

# 3rd-party modules
from lxml.builder import E

# local modules
from jnpr.junos.utils.util import Util
from jnpr.junos.utils.scp import SCP
from jnpr.junos.utils.ftp import FTP
from jnpr.junos.exception import SwRollbackError, RpcTimeoutError, RpcError

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
      * rollback: same as 'request software rollback'
      * inventory: (property) provides file info for current and rollback
        images on the device
    """

    def __init__(self, dev):
        Util.__init__(self, dev)
        self._dev = dev
        self._RE_list = [
            x for x in dev.facts.keys() if x.startswith('version_RE')]
        self._multi_RE = bool(len(self._RE_list) > 1)
        self._multi_VC = bool(
            self._multi_RE is True and dev.facts.get('vc_capable') is True and
            dev.facts.get('vc_mode') != 'Disabled')
        self._mixed_VC = bool(dev.facts.get('vc_mode') == 'Mixed')

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
        Computes the SHA1 checksum value on the local package file.

        :param str package:
          File-path to the package (\*.tgz) file on the local server

        :returns: SHA1 checksum (str)
        :raises IOError: when **package** file does not exist
        """
        return _hashfile(open(package, 'rb'), hashlib.sha1())

    @classmethod
    def progress(cls, dev, report):
        """ simple progress report function """
        print (dev.hostname + ": " + report)

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
          Callback function to indicate progress.  If set to ``True``
          uses :meth:`scp._scp_progress` for basic reporting by default.
          See that class method for details.
        """
        # execute FTP when connection mode if telnet
        if hasattr(self._dev, '_mode') and self._dev._mode=='telnet':
            with FTP(self._dev) as ftp:
                ftp.put(package, remote_path)
        else:
            # execute the secure-copy with the Python SCP module
            with SCP(self._dev, progress=progress) as scp:
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

        if isinstance(remote_package, (list, tuple)) and self._mixed_VC:
            args = dict(no_validate=True, set=remote_package)
        else:
            args = dict(no_validate=True, package_name=remote_package)
        args.update(kvargs)

        rsp = self.rpc.request_package_add(**args)

        got = rsp.getparent()
        rc = int(got.findtext('package-result').strip())

        # return True if rc == 0 else got.findtext('output').strip()
        return True if rc == 0 else False

    # -------------------------------------------------------------------------
    # validate - perform 'request' operation to validate the package
    # -------------------------------------------------------------------------

    def validate(self, remote_package, **kwargs):
        """
        Issues the 'request' operation to validate the package against the
        config.

        :returns:
            * ``True`` if validation passes
            * error (str) otherwise
        """
        rsp = self.rpc.request_package_validate(
            package_name=remote_package, **kwargs).getparent()
        errcode = int(rsp.findtext('package-result'))
        return True if 0 == errcode else rsp.findtext('output').strip()

    def remote_checksum(self, remote_package, timeout=300):
        """
        Computes the MD5 checksum on the remote device.

        :param str remote_package:
            The file-path on the remote Junos device

        :param int timeout:
          The amount of time (seconds) before declaring an RPC timeout.
          The default RPC timeout is generally around 30 seconds.  So this
          :timeout: value will be used in the context of the checksum process.
          Defaults to 5 minutes (5*60=300)

        :returns:
            * The MD5 checksum string
            * ``False`` when the **remote_package** is not found.

        :raises RpcError: RPC errors other than **remote_package** not found.
        """
        try:
            rsp = self.rpc.get_checksum_information(path=remote_package, dev_timeout=timeout)
            return rsp.findtext('.//checksum').strip()
        except RpcError as e:

            # e.errs is list of dictionaries
            if hasattr(e, 'errs') and \
                    list(filter(lambda x: 'No such file or directory' in x['message'], e.errs)):
                return None
            else:
                raise

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
            call-back function for progress updates. If set to ``True`` uses
          :meth:`sw.progress` for basic reporting by default.
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
            if progress is True:
                self.progress(self._dev, report)
            elif callable(progress):
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

    def install(self, package=None, pkg_set=None, remote_path='/var/tmp', progress=None,
                validate=False, checksum=None, cleanfs=True, no_copy=False,
                timeout=1800, **kwargs):
        """
        Performs the complete installation of the **package** that includes the
        following steps:

        1. computes the local MD5 checksum if not provided in :checksum:
        2. performs a storage cleanup if :cleanfs: is True
        3. SCP copies the package to the :remote_path: directory
        4. computes remote MD5 checksum and matches it to the local value
        5. validates the package if :validate: is True
        6. installs the package

        .. warning:: This process has been validated on the following deployments.

                      Tested:

                      * Single RE devices (EX, QFX, MX, SRX).
                      * MX dual-RE
                      * EX virtual-chassis when all same HW model
                      * QFX virtual-chassis when all same HW model
                      * QFX/EX mixed virtual-chassis
                      * Mixed mode VC

                      Known Restrictions:

                      * SRX cluster
                      * MX virtual-chassis

        You can get a progress report on this process by providing a **progress**
        callback.

        .. note:: You will need to invoke the :meth:`reboot` method explicitly to reboot
                  the device.

        :param str package:
          The file-path to the install package tarball on the local filesystem

        :param list pkg_set:
          The file-paths as list/tuple of the install package tarballs on the local
          filesystem which will be installed on mixed VC setup.

        :param str remote_path:
          The directory on the Junos device where the package file will be
          SCP'd to or where the package is stored on the device; the default is ``/var/tmp``.

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

          If set to ``True``, it uses :meth:`sw.progress`
          for basic reporting by default.

        :param bool no_copy:
          When ``True`` the software package will not be SCP'd to the device.
          Default is ``False``.

        :param int timeout:
          The amount of time (seconds) before declaring an RPC timeout.  This
          argument was added since most of the time the "package add" RPC
          takes a significant amount of time.  The default RPC timeout is
          generally around 30 seconds.  So this :timeout: value will be
          used in the context of the SW installation process.  Defaults to
          30 minutes (30*60=1800)

        :param bool force_host:
          (Optional) Force the addition of host software package or bundle
          (ignore warnings) on the QFX5100 device.
        """
        def _progress(report):
            if progress is True:
                self.progress(self._dev, report)
            elif callable(progress):
                progress(self._dev, report)

        # ---------------------------------------------------------------------
        # perform a 'safe-copy' of the image to the remote device
        # ---------------------------------------------------------------------

        if package is None and pkg_set is None:
            raise TypeError(
                'install() takes atleast 1 argument package or pkg_set')

        if no_copy is False:
            copy_ok = True
            if (sys.version<'3' and isinstance(package, (str, unicode))) or isinstance(package, str):
                copy_ok = self.safe_copy(package, remote_path=remote_path,
                                         progress=progress, cleanfs=cleanfs,
                                         checksum=checksum)
                if copy_ok is False:
                    return False

            elif isinstance(pkg_set, (list, tuple)) and len(pkg_set) > 0:
                for pkg in pkg_set:
                    # To disable cleanfs after 1st iteration
                    cleanfs = cleanfs and pkg_set.index(pkg) == 0
                    copy_ok = self.safe_copy(pkg, remote_path=remote_path,
                                             progress=progress,
                                             cleanfs=cleanfs,
                                             checksum=checksum)
                    if copy_ok is False:
                        return False
            else:
                raise ValueError(
                    'proper value either package or pkg_set is missing')
        # ---------------------------------------------------------------------
        # at this point, the file exists on the remote device
        # ---------------------------------------------------------------------
        if package is not None:
            remote_package = remote_path + '/' + path.basename(package)
            if validate is True:  # in case of Mixed VC it cant be used
                _progress(
                    "validating software against current config,"
                    " please be patient ...")
                v_ok = self.validate(remote_package, dev_timeout=timeout)
                if v_ok is not True:
                    return v_ok  # will be the string of output

            if self._multi_RE is False:
                # simple case of device with only one RE
                _progress("installing software ... please be patient ...")
                add_ok = self.pkgadd(
                    remote_package,
                    dev_timeout=timeout,
                    **kwargs)
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
                        ok &= self.pkgadd(
                            remote_package,
                            member=vc_id,
                            dev_timeout=timeout,
                            **kwargs)
                    return ok
                else:
                    # then this is a device with two RE that supports the "re0"
                    # and "re1" options to the command (M, MX tested only)
                    ok = True
                    _progress(
                        "installing software on RE0 ... please be patient ...")
                    ok &= self.pkgadd(
                        remote_package,
                        re0=True,
                        dev_timeout=timeout,
                        **kwargs)
                    _progress(
                        "installing software on RE1 ... please be patient ...")
                    ok &= self.pkgadd(
                        remote_package,
                        re1=True,
                        dev_timeout=timeout,
                        **kwargs)
                    return ok

        elif isinstance(pkg_set, (list, tuple)) and self._mixed_VC:
            pkg_set = [
                remote_path +
                '/' +
                path.basename(pkg) for pkg in pkg_set]
            _progress("installing software ... please be patient ...")
            add_ok = self.pkgadd(pkg_set, dev_timeout=timeout, **kwargs)
            return add_ok

    # -------------------------------------------------------------------------
    # reboot - system reboot
    # -------------------------------------------------------------------------

    def reboot(self, in_min=0, at=None):
        """
        Perform a system reboot, with optional delay (in minutes) or at
        a specified date and time.

        If the device is equipped with dual-RE, then both RE will be
        rebooted.  This code also handles EX/QFX VC.

        :param int in_min: time (minutes) before rebooting the device.

        :param str at: date and time the reboot should take place. The
            string must match the junos cli reboot syntax

        :returns:
            * reboot message (string) if command successful

        :raises RpcError: when command is not successful.

        .. todo:: need to better handle the exception event.
        """
        if in_min >= 0 and at is None:
            cmd = E('request-reboot', E('in', str(in_min)))
        else:
            cmd = E('request-reboot', E('at', str(at)))

        if self._multi_RE is True and self._multi_VC is False:
            cmd.append(E('both-routing-engines'))
        elif self._mixed_VC is True:
            cmd.append(E('all-members'))
        try:
            rsp = self.rpc(cmd)
            got = rsp.getparent().findtext('.//request-reboot-status').strip()
            return got
        except RpcTimeoutError as err:
            raise err
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
        rebooted.  This code also handles EX/QFX VC.

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
        Issues the 'request' command to do the rollback and returns the string
        output of the results.

        :returns:
            Rollback results (str)
        """
        rsp = self.rpc.request_package_rollback()
        fail_list = ['Cannot rollback', 'rollback aborted']
        multi = rsp.xpath('//multi-routing-engine-item')
        if multi:
            rsp = {}
            for x in multi:
                re = x.findtext('re-name')
                output = x.findtext('output')
                if any(x in output for x in fail_list):
                    raise SwRollbackError(re=re, rsp=output)
                else:
                    rsp[re] = output
            return str(rsp)
        else:
            output = rsp.xpath('//output')[0].text
            if any(x in output for x in fail_list):
                raise SwRollbackError(rsp=output)
            else:
                return output

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
