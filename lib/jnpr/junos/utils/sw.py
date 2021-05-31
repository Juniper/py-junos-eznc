# stdlib
from __future__ import print_function
import hashlib
import re
from os import path
import sys

try:
    # Python 3.x
    from urllib.parse import urlparse
except ImportError:
    # Python 2.x
    from urlparse import urlparse

# 3rd-party modules
from lxml.builder import E
from lxml import etree

# local modules
from jnpr.junos.decorators import timeoutDecorator
from jnpr.junos.utils.util import Util
from jnpr.junos.utils.scp import SCP
from jnpr.junos.utils.ftp import FTP
from jnpr.junos.utils.start_shell import StartShell
from jnpr.junos.exception import SwRollbackError, RpcTimeoutError, RpcError
from ncclient.xml_ import NCElement
from jnpr.junos import jxml as JXML

"""
Software Installation Utilities
"""

__all__ = ["SW"]


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
        self._RE_list = []
        if "junos_info" in dev.facts and dev.facts["junos_info"] is not None:
            self._RE_list = list(dev.facts["junos_info"].keys())
        else:
            self._RE_list = [x for x in dev.facts.keys() if x.startswith("version_RE")]
        self._multi_RE = bool(dev.facts.get("2RE"))
        # Branch SRX in an SRX cluster doesn't really support multi_RE
        # functionality for SW.
        if (
            dev.facts.get("personality", "") == "SRX_BRANCH"
            and dev.facts.get("srx_cluster") is True
        ):
            self._multi_RE = False
        self._multi_VC = bool(
            self._multi_RE is True
            and dev.facts.get("vc_capable") is True
            and dev.facts.get("vc_mode") != "Disabled"
        )
        self._mixed_VC = bool(dev.facts.get("vc_mode") == "Mixed")
        # The devices which currently support single-RE ISSU, communicate with
        #  the new Junos VM using internal IP 128.0.0.63.
        # Therefore, the 'localre' value in the 'current_re' fact can currently
        # be used to check for this capability.
        # {master: 0}
        #  user @ s0 > file show / etc / hosts.junos | match localre
        #  128.0.0.63               localre
        self._single_re_issu = bool(
            "current_re" in dev.facts and "localre" in dev.facts["current_re"]
        )
        self.log = lambda report: None

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
        return _hashfile(open(package, "rb"), hashlib.sha256())

    @classmethod
    def local_md5(cls, package):
        """
        Computes the MD5 checksum value on the local package file.

        :param str package:
          File-path to the package (\*.tgz) file on the local server

        :returns: MD5 checksum (str)
        :raises IOError: when **package** file does not exist
        """
        return _hashfile(open(package, "rb"), hashlib.md5())

    @classmethod
    def local_sha1(cls, package):
        """
        Computes the SHA1 checksum value on the local package file.

        :param str package:
          File-path to the package (\*.tgz) file on the local server

        :returns: SHA1 checksum (str)
        :raises IOError: when **package** file does not exist
        """
        return _hashfile(open(package, "rb"), hashlib.sha1())

    @classmethod
    def local_checksum(cls, package, algorithm="md5"):
        """
        Computes the checksum value on the local package file.

        :param str package:
          File-path to the package (\*.tgz) file on the local server
        :param str algorithm:
          The algorithm to use for computing the checksum. Valid values are:
          'md5', 'sha1', and 'sha256'. Defaults to 'md5'.

        :returns: checksum (str)
        :raises IOError: when **package** file does not exist
        """
        if algorithm == "md5":
            return cls.local_md5(package)
        elif algorithm == "sha1":
            return cls.local_sha1(package)
        elif algorithm == "sha256":
            return cls.local_sha256(package)
        else:
            raise ValueError("Unknown checksum algorithm: %s" % (algorithm))

    @classmethod
    def progress(cls, dev, report):
        """simple progress report function"""
        print(dev.hostname + ": " + report)

    # -------------------------------------------------------------------------
    # put - Copy the image onto the device
    # -------------------------------------------------------------------------

    def put(self, package, remote_path="/var/tmp", progress=None):
        """
        SCP or FTP 'put' the package file from the local server to the remote
        device.

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
        if hasattr(self._dev, "_mode") and self._dev._mode == "telnet":
            with FTP(self._dev) as ftp:
                ftp.put(package, remote_path)
        else:
            # execute the secure-copy with the Python SCP module
            with SCP(self._dev, progress=progress) as scp:
                scp.put(package, remote_path)

    # -------------------------------------------------------------------------
    # pkgadd - used to perform the 'request system software add ...'
    # -------------------------------------------------------------------------

    def pkgadd(self, remote_package, vmhost=False, **kvargs):
        """
        Issue the RPC equivalent of the 'request system software add' command
        or the 'request vmhost software add' command on the package.
        If vhmhost=False, the <request-package-add> RPC is used and the
        The "no-validate" options is set.  If you want to validate
        the image, do that using the specific :meth:`validate` method.
        If vmhost=True, the <request-vmhost-package-add> RPC is used.

        If you want to reboot the device, invoke the :meth:`reboot` method
        after installing the software rather than passing the ``reboot=True``
        parameter.

        :param str remote_package:
          The file-path to the install package on the remote (Junos) device.


        :param bool vhmhost:
          (Optional) A boolean indicating if this is a software update of the
          vhmhost. The default is ``vmhost=False``.

        :param dict kvargs:
          Any additional parameters to the 'request' command can
          be passed within **kvargs**, following the RPC syntax
          methodology (dash-2-underscore,etc.)

        .. warning:: Refer to the restrictions listed in :meth:`install`.
        """

        if vmhost is False:
            if isinstance(remote_package, (list, tuple)) and self._mixed_VC:
                args = dict(no_validate=True, set=remote_package)
            else:
                args = dict(no_validate=True, package_name=remote_package)
            args.update(kvargs)
            rsp = self.rpc.request_package_add(**args)
        else:
            rsp = self.rpc.request_vmhost_package_add(
                package_name=remote_package, **kvargs
            )

        return self._parse_pkgadd_response(rsp)

    # -------------------------------------------------------------------------
    # pkgaddNSSU - used to perform NSSU upgrade
    # -------------------------------------------------------------------------

    def pkgaddNSSU(self, remote_package, **kvargs):
        """
        Issue the 'request system software nonstop-upgrade' command on the
        package.

        :param str remote_package:
          The file-path to the install package on the remote (Junos) device.
        """

        rsp = self.rpc.request_package_nonstop_upgrade(
            package_name=remote_package, **kvargs
        )
        return self._parse_pkgadd_response(rsp)

    # -------------------------------------------------------------------------
    # pkgaddISSU - used to perform ISSU upgrade
    # -------------------------------------------------------------------------

    def pkgaddISSU(self, remote_package, vmhost=False, **kvargs):
        """
        Issue the RPC equivalent of the
        'request system software in-service-upgrade' command
        or the 'request vmhost software in-service-upgrade' command on the
        package. If vhmhost=False, the <request-package-in-service-upgrade>
        RPC is used. If vmhost=True, the
        <request-vmhost-package-in-service-upgrade> RPC is used.

        :param str remote_package:
          The file-path to the install package on the remote (Junos) device.


        :param bool vmhost:
          (Optional) A boolean indicating if this is a software update of the
          vhmhost. The default is ``vmhost=False``.
        """

        if vmhost is False:
            rsp = self.rpc.request_package_in_service_upgrade(
                package_name=remote_package, **kvargs
            )
        else:
            rsp = self.rpc.request_vmhost_package_in_service_upgrade(
                package_name=remote_package, **kvargs
            )
        return self._parse_pkgadd_response(rsp)

    def _parse_pkgadd_response(self, rsp):
        got = rsp.getparent()
        # If <package-result> is not present, then assume success.
        # That is, assume <package-result>0</package-result>
        rc = 0
        package_result = got.findtext("package-result")
        if package_result is None:
            self.log(
                "software pkgadd response is missing package-result "
                "element. Assuming success."
            )
        else:
            for result in got.findall("package-result"):
                rc += int(result.text.strip())
        output_msg = "\n".join(
            [i.text for i in got.findall("output") if i.text is not None]
        )
        self.log("software pkgadd package-result: %s\nOutput: %s" % (rc, output_msg))
        return rc == 0, output_msg

    # -------------------------------------------------------------------------
    # validate - perform 'request' operation to validate the package
    # -------------------------------------------------------------------------

    def validate(self, remote_package, issu=False, nssu=False, **kwargs):
        """
        Issues the 'request' operation to validate the package against the
        config.

        :returns:
            * ``True`` if validation passes. i.e return code (rc) value is 0
            * * ``False`` otherwise
        """
        if nssu and not self._issu_nssu_requirement_validation():
            return False
        if issu:
            if not self._issu_requirement_validation():
                return False
            rsp = self.rpc.check_in_service_upgrade(
                package_name=remote_package, **kwargs
            ).getparent()
        else:
            rsp = self.rpc.request_package_validate(
                package_name=remote_package, **kwargs
            ).getparent()
        rc = int(rsp.findtext("package-result"))
        output_msg = "\n".join(
            [i.text for i in rsp.findall("output") if i.text is not None]
        )
        self.log("software validate package-result: %s\nOutput: %s" % (rc, output_msg))
        return 0 == rc

    def _issu_requirement_validation(self):
        """
        Checks:
            * The master Routing Engine and backup Routing Engine must be
                running the same software version before you can perform a
                unified ISSU.
            * Check GRES is enabled
            * Check NSR is enabled
            * Check commit synchronize is enabled
            * Verify that NSR is configured on the master Routing Engine
                by using the "show task replication" command.
            * Verify that GRES is enabled on the backup Routing Engine
                by using the show system switchover command.

        :returns:
            * ``True`` if validation passes.
            * * ``False`` otherwise
        """
        self.log(
            "ISSU requirement validation: The master Routing Engine and\n"
            "backup Routing engine must be running the same software\n"
            "version before you can perform a unified ISSU."
        )
        if not (
            self._dev.facts["2RE"]
            and self._dev.facts["version_RE0"] == self._dev.facts["version_RE1"]
        ):
            self.log(
                "Requirement FAILED: The master Routing Engine (%s) and\n"
                "backup Routing Engine (%s) must be running the same\n"
                "software version before it can perform a unified ISSU"
                % (self._dev.facts["version_RE0"], self._dev.facts["version_RE1"])
            )
            return False
        if not self._issu_nssu_requirement_validation():
            return False
        self.log(
            "Verify that GRES is enabled on the backup Routing Engine\n"
            'by using the command "show system switchover"'
        )
        output = ""
        try:
            op = self._dev.rpc.request_shell_execute(
                routing_engine="backup", command="cli show system switchover"
            )
            if op.findtext(".//switchover-state", default="").lower() == "on":
                self.log("Graceful switchover status is On")
                return True
            output = op.findtext(".//output", default="")
        except RpcError:
            # request-shell-execute rpc is not available for <14.1
            with StartShell(self._dev) as ss:
                ss.run("cli", "> ", timeout=5)
                if ss.run("request routing-engine " "login other-routing-engine")[0]:
                    # depending on user permission, prompt will go to either
                    # cli or shell, below line of code prompt will finally end
                    # up in cli mode
                    ss.run("cli", "> ", timeout=5)
                    data = ss.run("show system switchover", "> ", timeout=5)
                    output = data[1]
                    ss.run("exit")
                else:
                    self.log(
                        "Requirement FAILED: Not able run " '"show system switchover"'
                    )
                    return False
        gres_status = re.search(r"Graceful switchover: (\w+)", output, re.I)
        if not (gres_status is not None and gres_status.group(1).lower() == "on"):
            self.log("Requirement FAILED: Graceful switchover status " "is not On")
            return False
        self.log("Graceful switchover status is On")
        return True

    def _issu_nssu_requirement_validation(self):
        """
        Checks:
            * Check GRES is enabled
            * Check NSR is enabled
            * Check commit synchronize is enabled
            * Verify that NSR is configured on the master Routing Engine
                by using the "show task replication" command.

        :returns:
            * ``True`` if validation passes.
            * * ``False`` otherwise
        """
        self.log("Checking GRES configuration")
        conf = self._dev.rpc.get_config(
            filter_xml=etree.XML(
                """
                   <configuration>
                       <chassis>
                           <redundancy>
                               <graceful-switchover/>
                           </redundancy>
                       </chassis>
                   </configuration>"""
            ),
            options={
                "database": "committed",
                "inherit": "inherit",
                "commit-scripts": "apply",
            },
        )
        if conf.find("chassis/redundancy/graceful-switchover") is None:
            self.log("Requirement FAILED: GRES is not Enabled " "in configuration")
            return False
        self.log("Checking commit synchronize configuration")
        conf = self._dev.rpc.get_config(
            filter_xml=etree.XML(
                """
            <configuration>
                <system>
                    <commit>
                        <synchronize/>
                    </commit>
                </system>
            </configuration>"""
            ),
            options={
                "database": "committed",
                "inherit": "inherit",
                "commit-scripts": "apply",
            },
        )
        if conf.find("system/commit/synchronize") is None:
            self.log(
                "Requirement FAILED: commit synchronize is not "
                "Enabled in configuration"
            )
            return False
        self.log("Checking NSR configuration")
        conf = self._dev.rpc.get_config(
            filter_xml=etree.XML(
                """
                   <configuration>
                       <routing-options>
                           <nonstop-routing/>
                       </routing-options>
                   </configuration>
                   """
            ),
            options={
                "database": "committed",
                "inherit": "inherit",
                "commit-scripts": "apply",
            },
        )
        if conf.find("routing-options/nonstop-routing") is None:
            self.log("Requirement FAILED: NSR is not Enabled in configuration")
            return False
        self.log(
            "Verifying that GRES status on the current Routing Engine "
            'is Enabled by using the "show task replication" command.'
        )
        op = self._dev.rpc.get_routing_task_replication_state()
        if not (
            op.findtext("task-gres-state") == "Enabled"
            and op.findtext("task-re-mode") == "Master"
        ):
            self.log(
                "Requirement FAILED: Either Stateful Replication is not "
                "Enabled or RE mode\nis not Master"
            )
            return False
        return True

    def remote_checksum(self, remote_package, timeout=300, algorithm="md5"):
        """
        Computes a checksum of the remote_package file on the remote device.

        :param str remote_package:
          The file-path on the remote Junos device
        :param int timeout:
          The amount of time (seconds) before declaring an RPC timeout.
          The default RPC timeout is generally around 30 seconds.  So this
          :timeout: value will be used in the context of the checksum process.
          Defaults to 5 minutes (5*60=300)
        :param str algorithm:
          The algorithm to use for computing the checksum. Valid values are:
          'md5', 'sha1', and 'sha256'. Defaults to 'md5'.

        :returns:
            * The checksum string
            * ``None`` when the **remote_package** is not found.

        :raises RpcError: RPC errors other than **remote_package** not found.
        """
        kwargs = {"path": remote_package, "dev_timeout": timeout, "normalize": True}
        try:
            if algorithm == "md5":
                rsp = self.rpc.get_checksum_information(**kwargs)
            elif algorithm == "sha1":
                rsp = self.rpc.get_sha1_checksum_information(**kwargs)
            elif algorithm == "sha256":
                rsp = self.rpc.get_sha256_checksum_information(**kwargs)
            else:
                raise ValueError("Unknown checksum algorithm: %s" % (algorithm))
            return rsp.findtext(".//checksum")
        except RpcError as e:
            if "No such file or directory" in getattr(e, "message", ""):
                return None
            else:
                raise

    # -------------------------------------------------------------------------
    # safe_copy - copies the package and performs checksum
    # -------------------------------------------------------------------------

    def safe_copy(
        self,
        package,
        remote_path="/var/tmp",
        progress=None,
        cleanfs=True,
        cleanfs_timeout=300,
        checksum=None,
        checksum_timeout=300,
        checksum_algorithm="md5",
        force_copy=False,
    ):
        """
        Copy the install package safely to the remote device.  By default
        this means to clean the filesystem to make space, perform the
        secure-copy, and then verify the checksum.

        :param str package:
            file-path to package on local filesystem
        :param str remote_path:
            file-path to directory on remote device
        :param func progress:
            call-back function for progress updates. If set to ``True`` uses
            :meth:`sw.progress` for basic reporting by default.
        :param bool cleanfs:
            When ``True`` (default) perform a
            "request system storage cleanup" on the device.
        :param int cleanfs_timeout:
            Number of seconds (default 300) to wait for the
            "request system storage cleanup" to complete.
        :param str checksum:
            This is the checksum string as computed on the local system.
            This value will be used to compare the checksum on the
            remote Junos device.
        :param int checksum_timeout:
            Number of seconds (default 300) to wait for the calculation of the
            checksum on the remote Junos device.
        :param str checksum_algorithm:
            The algorithm to use for computing the checksum. Valid values are:
            'md5', 'sha1', and 'sha256'. Defaults to 'md5'.
        :param bool force_copy:
            When ``True`` perform the copy even if the package is already
            present at the remote_path on the device. When ``False`` (default)
            if the package is already present at the remote_path, and the local
            checksum matches the remote checksum, then skip the copy to
            optimize time.

        :returns:
            * ``True`` when the copy was successful
            * ``False`` otherwise
        """

        def _progress(report):
            if progress is True:
                self.progress(self._dev, report)
            elif callable(progress):
                progress(self._dev, report)

        if checksum is None:
            _progress("computing checksum on local package: %s" % (package))
            try:
                checksum = SW.local_checksum(package, algorithm=checksum_algorithm)
            except IOError:
                _progress(
                    "error computing checksum on local package: %s. "
                    "Ensure the local package exists." % (package)
                )
                return False

        if checksum is None:
            _progress(
                "Unable to calculate the checksum on local package: %s." % (package)
            )
            return False

        if cleanfs is True:
            _progress("cleaning filesystem ...")
            try:
                self.rpc.request_system_storage_cleanup(dev_timeout=cleanfs_timeout)
            except RpcError as err:
                _progress("Problem cleaning filesystem: %s" % (str(err)))
                return False

        # Calculate the remote package name.
        remote_package = remote_path + "/" + path.basename(package)

        remote_checksum = None
        # Check to see if the package file already exists on the remote
        # device by trying to get the checksum.
        if force_copy is False:
            _progress(
                "before copy, computing checksum on remote package: %s" % remote_package
            )
            remote_checksum = self.remote_checksum(
                remote_package, timeout=checksum_timeout, algorithm=checksum_algorithm
            )

        if remote_checksum != checksum:
            # Need to copy the file.
            self.put(package, remote_path=remote_path, progress=progress)

            # Now validate checksum of the recently copied file.
            _progress(
                "after copy, computing checksum on remote package: %s" % remote_package
            )
            remote_checksum = self.remote_checksum(
                remote_package, timeout=checksum_timeout, algorithm=checksum_algorithm
            )

        if remote_checksum != checksum:
            _progress("checksum check failed.")
            return False

        _progress("checksum check passed.")
        return True

    # -------------------------------------------------------------------------
    # install - complete installation process, but not reboot
    # -------------------------------------------------------------------------

    def install(
        self,
        package=None,
        pkg_set=None,
        remote_path="/var/tmp",
        progress=None,
        validate=False,
        checksum=None,
        cleanfs=True,
        no_copy=False,
        issu=False,
        nssu=False,
        timeout=1800,
        cleanfs_timeout=300,
        checksum_timeout=300,
        checksum_algorithm="md5",
        force_copy=False,
        all_re=True,
        vmhost=False,
        **kwargs
    ):
        """
        Performs the complete installation of the **package** that includes the
        following steps:

        1. If :package: is a URL, or :no_copy: is True, skip to step 8.
        2. computes the checksum of :package: or :pgk_set: on the local host
           if :checksum: was not provided.
        3. performs a storage cleanup on the remote Junos device if :cleanfs:
           is ``True``
        4. Attempts to compute the checksum of the :package: filename in the
           :remote_path: directory of the remote Junos device if the
           :force_copy: argument is ``False``
        5. SCP or FTP copies the :package: file from the local host to the
           :remote_path: directory on the remote Junos device under any of the
           following conditions:

           a) The :force_copy: argument is ``True``
           b) The :package: filename doesn't already exist in the
              :remote_path: directory of the remote Junos device.
           c) The checksum computed in step 2 does not match the checksum
              computed in step 4.
        6. If step 5 was executed, computes the checksum of the :package:
           filename in the :remote_path: directory of the remote Junos device.
        7. Validates the checksum computed in step 2 matches the checksum
           computed in step 6.
        8. validates the package if :validate: is True
        9. installs the package

        .. warning:: This process has been validated on the following
                     deployments.

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

        You can get a progress report on this process by providing a
        **progress** callback.

        .. note:: You will need to invoke the :meth:`reboot` method explicitly
                   to reboot the device.

        :param str package:
          Either the full file path to the install package tarball on the local
          (PyEZ host's) filesystem OR a URL (from the target device's
          perspcective) from which the device retrieves installed. When the
          value is a URL, then the :no_copy: and :remote_path: values are
          unused. The acceptable formats for a URL value may be found at:
          https://www.juniper.net/documentation/en_US/junos/topics/concept/junos-software-formats-filenames-urls.html

        :param list pkg_set:
          A list/tuple of :package: values which will be installed on a mixed
          VC setup.

        :param str remote_path:
          If the value of :package: or :pkg_set: is a file path on the local
          (PyEZ host's) filesystem, then the image is copied from the local
          filesystem to the :remote_path: directory on the target Junos
          device. The default is ``/var/tmp``. If the value of :package: or
          :pkg_set: is a URL, then the value of :remote_path: is unused.

        :param func progress:
          If provided, this is a callback function with a function prototype
          given the Device instance and the report string::

            def myprogress(dev, report):
              print "host: %s, report: %s" % (dev.hostname, report)

          If set to ``True``, it uses :meth:`sw.progress`
          for basic reporting by default.

        :param bool validate:
          When ``True`` this method will perform a config validation against
          the new image

        :param str checksum:
          hexdigest of the package file. If this is not provided, then this
          method will perform the calculation. If you are planning on using the
          same image for multiple updates, you should consider using the
          :meth:`local_checksum` method to pre calculate this value and then
          provide to this method.

        :param bool cleanfs:
          When ``True`` will perform a 'storage cleanup' before copying the
          file to the device.  Default is ``True``.

        :param bool no_copy:
          When the value of :package: or :pkg_set is not a URL, and the value
          of :no_copy: is ``True`` the software package will not be copied to
          the device and is presumed to already exist on the :remote_path:
          directory of the target Junos device. When the value of :no_copy: is
          ``False`` (the default), then the package is copied from the local
          PyEZ host to the :remote_path: directory of the target Junos device.
          If the value of :package: or :pkg_set: is a URL, then the value of
          :no_copy: is unused.

        :param bool issu:
          (Optional) When ``True`` allows unified in-service software upgrade
          (ISSU) feature enables you to upgrade between two different Junos OS
          releases with no disruption on the control plane and with minimal
          disruption of traffic.

        :param bool nssu:
          (Optional) When ``True`` allows nonstop software upgrade (NSSU)
          enables you to upgrade the software running on a Juniper Networks
          EX Series Virtual Chassis or a Juniper Networks EX Series Ethernet
          Switch with redundant Routing Engines with a single command and
          minimal disruption to network traffic.

        :param int timeout:
          (Optional) The amount of time (seconds) to wait for the
          :package: installation to complete before declaring an RPC
          timeout.  This argument was added since most of the time the
          "package add" RPC takes a significant amount of time.  The default
          RPC timeout is 30 seconds.  So this :timeout: value will be
          used in the context of the SW installation process.  Defaults to
          30 minutes (30*60=1800)

        :param int cleanfs_timeout:
          (Optional) Number of seconds (default 300) to wait for the
          "request system storage cleanup" to complete.

        :param int checksum_timeout:
          (Optional) Number of seconds (default 300) to wait for the
          calculation of the checksum on the remote Junos device.
        :param str checksum_algorithm:
          (Optional) The algorithm to use for computing the checksum.
          Valid values are: 'md5', 'sha1', and 'sha256'. Defaults to 'md5'.

        :param bool force_copy:
          (Optional) When ``True`` perform the copy even if :package: is
          already present at the :remote_path: directory on the remote Junos
          device. When ``False`` (default) if the :package: is already present
          at the :remote_path:, AND the local checksum matches the remote
          checksum, then skip the copy to optimize time.

        :param bool all_re:
          (Optional) When ``True`` (default) install the package on
          all Routing Engines of the Junos device. When ``False`` perform
          the software install only on the current Routing Engine.

        :param bool vmhost:
          (Optional) A boolean indicating if this is a software update of the
          vhmhost. The default is ``vmhost=False``.

        :param kwargs **kwargs:
          (Optional) Additional keyword arguments are passed through to the
          "package add" RPC.

        :returns: tuple(<status>, <msg>)
            * status : ``True`` when the installation is successful and ``False`` otherwise
            * msg : msg received as response or error message created
        """
        if issu is True and nssu is True:
            raise TypeError("install function can either take issu or nssu not both")
        elif (issu is True or nssu is True) and (
            self._multi_RE is not True and self._single_re_issu is not True
        ):
            raise TypeError("ISSU/NSSU requires Multi RE setup")

        def _progress(report):
            if progress is True:
                self.progress(self._dev, report)
            elif callable(progress):
                progress(self._dev, report)

        self.log = _progress

        # ---------------------------------------------------------------------
        # Before doing anything, Do check if any pending install exists.
        # ---------------------------------------------------------------------
        try:
            pending_install = self._dev.rpc.request_package_checks_pending_install()
            msg = pending_install.text
            if (
                msg
                and msg.strip() != ""
                and pending_install.getparent().findtext("package-result").strip()
                == "1"
            ):
                _progress(msg)
                return False
        except RpcError:
            _progress(
                "request-package-checks-pending-install rpc is not "
                "supported on given device"
            )
        except Exception as ex:
            _progress("check pending install failed with exception: %s" % ex)
            # Continue with software installation

        # ---------------------------------------------------------------------
        # perform a 'safe-copy' of the image to the remote device
        # ---------------------------------------------------------------------

        if package is None and pkg_set is None:
            raise TypeError(
                "install() requires either the package or pkg_set argument."
            )

        remote_pkg_set = []
        if (sys.version < "3" and isinstance(package, (str, unicode))) or isinstance(
            package, str
        ):
            pkg_set = [package]
        if isinstance(pkg_set, (list, tuple)) and len(pkg_set) > 0:
            for pkg in pkg_set:
                parsed_url = urlparse(pkg)
                if parsed_url.scheme == "":
                    if no_copy is False:
                        # To disable cleanfs after 1st iteration
                        cleanfs = cleanfs and pkg_set.index(pkg) == 0
                        copy_ok = self.safe_copy(
                            pkg,
                            remote_path=remote_path,
                            progress=progress,
                            cleanfs=cleanfs,
                            checksum=checksum,
                            cleanfs_timeout=cleanfs_timeout,
                            checksum_timeout=checksum_timeout,
                            checksum_algorithm=checksum_algorithm,
                            force_copy=force_copy,
                        )
                        if copy_ok is False:
                            return False, "Package %s couldn't be copied" % pkg
                    pkg = remote_path + "/" + path.basename(pkg)

                remote_pkg_set.append(pkg)
        else:
            raise ValueError("proper value for either package or pkg_set is missing")
        # ---------------------------------------------------------------------
        # at this point, the file exists on the remote device
        # or will be loaded directly from a URL.
        # ---------------------------------------------------------------------

        if len(remote_pkg_set) == 1:
            remote_package = remote_pkg_set[0]
            # validate can't be used in the case of a Mixed VC
            # With vmhost=True, validate is handled in the package add.
            if validate is True:
                if self._mixed_VC is False and vmhost is not True:
                    _progress(
                        "validating software against current config,"
                        " please be patient ..."
                    )
                    v_ok = self.validate(
                        remote_package, issu, nssu, dev_timeout=timeout
                    )
                    if v_ok is not True:
                        return v_ok, "Package validation failed"
            else:
                if vmhost is True:
                    # Need to pass the no_validate option via kwargs.
                    kwargs.update({"no_validate": True})

            if issu is True:
                _progress("ISSU: installing software ... please be patient ...")
                return self.pkgaddISSU(
                    remote_package, vmhost=vmhost, dev_timeout=timeout, **kwargs
                )
            elif nssu is True:
                _progress("NSSU: installing software ... please be patient ...")
                return self.pkgaddNSSU(remote_package, dev_timeout=timeout, **kwargs)
            elif self._multi_RE is False or all_re is False:
                # simple case of single RE upgrade.
                _progress("installing software ... please be patient ...")
                add_ok = self.pkgadd(
                    remote_package, vmhost=vmhost, dev_timeout=timeout, **kwargs
                )
                return add_ok
            else:
                # we need to update multiple devices
                if self._multi_VC is True:
                    ok = True, ""
                    # extract the VC number out of the _RE_list
                    vc_members = [
                        re.search("(\d+)", x).group(1)
                        for x in self._RE_list
                        if re.search("(\d+)", x)
                    ]
                    for vc_id in vc_members:
                        _progress(
                            "installing software on VC member: {} ... please "
                            "be patient ...".format(vc_id)
                        )
                        bool_ret, msg = self.pkgadd(
                            remote_package,
                            vmhost=vmhost,
                            member=vc_id,
                            dev_timeout=timeout,
                            **kwargs
                        )
                        ok = ok[0] and bool_ret, ok[1] + "\n" + msg
                    return ok
                else:
                    # then this is a device with two RE that supports the "re0"
                    # and "re1" options to the command (M, MX tested only)
                    _progress("installing software on RE0 ... please be patient ...")
                    ok = self.pkgadd(
                        remote_package,
                        vmhost=vmhost,
                        re0=True,
                        dev_timeout=timeout,
                        **kwargs
                    )
                    _progress("installing software on RE1 ... please be patient ...")
                    bool_ret, msg = self.pkgadd(
                        remote_package,
                        vmhost=vmhost,
                        re1=True,
                        dev_timeout=timeout,
                        **kwargs
                    )
                    ok = ok[0] and bool_ret, ok[1] + "\n" + msg
                    return ok

        elif len(remote_pkg_set) > 1 and self._mixed_VC:
            _progress("installing software ... please be patient ...")
            add_ok = self.pkgadd(
                remote_pkg_set, vmhost=vmhost, dev_timeout=timeout, **kwargs
            )
            return add_ok

    def _system_operation(
        self, cmd, in_min=0, at=None, all_re=True, other_re=False, vmhost=False
    ):
        """
        Send the rpc for actions like shutdown, reboot, halt  with optional
        delay (in minutes) or at a specified date and time.

        :param int in_min: time (minutes) before rebooting/shutting down the device.

        :param str at: date and time the reboot should take place. The
            string must match the junos cli reboot/poweroff/halt syntax

        :param bool all_re: In case of dual re or VC setup, function by default
            will reboot/shutdown all. If all is False will only reboot/shutdown connected device

        :param str on_node: In case of linux based device, function will by default
            reboot the whole device. If any specific node is mentioned,
            reboot will be performed on mentioned node

        :param str other_re: If the system has dual Routing Engines and this option is C(true),
            then the action is performed on the other REs in the system.

        :param bool vmhost:
            (Optional) A boolean indicating to run 'request vmhost reboot'.
            The default is ``vmhost=False``.

        :returns:
            * rpc response message (string) if command successful

        :raises RpcError: when command is not successful.
        """
        if other_re is True:
            if self._dev.facts["2RE"]:
                cmd = E("other-routing-engine")
        elif all_re is True:
            if self._multi_RE is True and vmhost is True:
                cmd.append(E("routing-engine", "both"))
            elif self._multi_RE is True and self._multi_VC is False:
                cmd.append(E("both-routing-engines"))
            elif self._mixed_VC is True:
                cmd.append(E("all-members"))
        if in_min >= 0 and at is None:
            cmd.append(E("in", str(in_min)))
        elif at is not None:
            cmd.append(E("at", str(at)))
        try:
            rsp = self.rpc(cmd, ignore_warning=True, normalize=True)
            if self._dev.facts["_is_linux"]:
                got = rsp.text
            else:
                got = rsp.getparent().findtext(".//request-reboot-status")
                if got is None:
                    # On some platforms stopping/rebooting
                    # REs produces <output> messages and
                    # <request-reboot-status> messages.
                    output_msg = "\n".join(
                        [
                            i.text
                            for i in rsp.getparent().xpath("//output")
                            if i.text is not None
                        ]
                    )
                    if output_msg is not "":
                        got = output_msg
            return got
        except Exception as err:
            raise err

    # -------------------------------------------------------------------------
    # reboot - system reboot
    # -------------------------------------------------------------------------
    def reboot(
        self, in_min=0, at=None, all_re=True, on_node=None, vmhost=False, other_re=False
    ):
        """
        Perform a system reboot, with optional delay (in minutes) or at
        a specified date and time.

        If the device is equipped with dual-RE, then both RE will be
        rebooted.  This code also handles EX/QFX VC.

        :param int in_min: time (minutes) before rebooting the device.

        :param str at: date and time the reboot should take place. The
            string must match the junos cli reboot syntax

        :param bool all_re: In case of dual re or VC setup, function by default
            will reboot all. If all is False will only reboot connected device

        :param str on_node: In case of linux based device, function will by default
            reboot the whole device. If any specific node is mentioned,
            reboot will be performed on mentioned node

        :param bool vmhost:
            (Optional) A boolean indicating to run 'request vmhost reboot'.
            The default is ``vmhost=False``.

        :param str other_re: If the system has dual Routing Engines and this option is C(true),
            then the action is performed on the other REs in the system.

        :returns:
            * reboot message (string) if command successful
        """
        if self._dev.facts["_is_linux"]:
            if on_node is None:
                cmd = E("request-shutdown-reboot")
            else:
                cmd = E("request-node-reboot")
                cmd.append(E("node", on_node))
        elif vmhost is True:
            cmd = E("request-vmhost-reboot")
        else:
            cmd = E("request-reboot")

        try:
            return self._system_operation(cmd, in_min, at, all_re, other_re, vmhost)
        except RpcTimeoutError as err:
            raise err
        except Exception as err:
            raise err

    # -------------------------------------------------------------------------
    # poweroff - system shutdown
    # -------------------------------------------------------------------------
    def poweroff(self, in_min=0, at=None, on_node=None, all_re=True, other_re=False):
        """
        Perform a system shutdown, with optional delay (in minutes) .

        If the device is equipped with dual-RE, then both RE will be
        shut down.  This code also handles EX/QFX VC.

        :param int in_min: time (minutes) before shutting down the device.

        :param str at: date and time the poweroff should take place. The
            string must match the junos cli poweroff syntax

        :param str on_node: In case of linux based device, function will by default
            shutdown the whole device. If any specific node is mentioned,
            shutdown will be performed on mentioned node

        :param bool all_re: In case of dual re or VC setup, function by default
            will shutdown all. If all is False will only shutdown connected device

        :param str other_re: If the system has dual Routing Engines and this option is C(true),
            then the action is performed on the other REs in the system.

        :returns:
            * power-off message (string) if command successful

        :raises RpcError: when command is not successful.

        .. todo:: need to better handle the exception event.
        """
        if self._dev.facts["_is_linux"]:
            if on_node is None:
                cmd = E("request-shutdown-power-off")
            else:
                cmd = E("request-node-power-off")
                cmd.append(E("node", on_node))
        else:
            cmd = E("request-power-off")
        try:
            return self._system_operation(
                cmd, in_min, at, all_re, other_re, vmhost=False
            )
        except Exception as err:
            if err.rsp.findtext(".//error-severity") != "warning":
                raise err

    # -------------------------------------------------------------------------
    # halt - system halt
    # -------------------------------------------------------------------------
    def halt(self, in_min=0, at=None, all_re=True, other_re=False):
        """
        Perform a system halt, with optional delay (in minutes) or at
        a specified date and time.

        :param int in_min: time (minutes) before halting the device.

        :param str at: date and time the halt should take place. The
            string must match the junos cli reboot syntax

        :param bool all_re: In case of dual re or VC setup, function by default
            will halt all. If all is False will only halt connected device

        :param str other_re: If the system has dual Routing Engines and this option is C(true),
            then the action is performed on the other REs in the system.

        :returns:
            * rpc response message (string) if command successful
        """
        if self._dev.facts["_is_linux"]:
            cmd = E("request-shutdown-halt")
        else:
            cmd = E("request-halt")

        try:
            return self._system_operation(
                cmd, in_min, at, all_re, other_re, vmhost=False
            )
        except Exception as err:
            raise err

    def zeroize(self, all_re=False, media=None):
        """
        Restore the system (configuration, log files, etc.) to a
        factory default state. This is the equivalent of the
        C(request system zeroize) CLI command.

        :param bool all_re: In case of dual re or VC setup, function by default
            will halt all. If all is False will only halt connected device

        :param str media: Overwrite media when performing the zeroize operation.

        :returns:
            * rpc response message (string) if command successful
        """
        cmd = E("request-system-zeroize")
        if all_re is False:
            if self._dev.facts["2RE"]:
                cmd = E("local")
            if media is True:
                cmd = E("media")

        # initialize an empty output message
        output_msg = ""

        try:
            # For zeroize we don't get a response similar to reboot, shutdown.
            # The response may come as a warning message only.
            # Code is added here to extract the warning message and append it.
            # Don't pass ignore warning true and handle the warning here.
            rsp = self.rpc(cmd, normalize=True)
        except RpcError as ex:
            if hasattr(ex, "xml"):
                if hasattr(ex, "errs"):
                    errors = ex.errs
                else:
                    errors = [ex]
                for err in errors:
                    if err.get("severity", "") != "warning":
                        # Not a warning (probably an error).
                        raise ex
                    output_msg += err.get("message", "") + "\n"
                rsp = ex.xml.getroottree().getroot()
                # 1) A normal response has been run through the XSLT
                #    transformation, but ex.xml has not. Do that now.
                encode = None if sys.version < "3" else "unicode"
                rsp = NCElement(
                    etree.tostring(rsp, encoding=encode), self._dev.transform()
                )._NCElement__doc
                # 2) Now remove all of the <rpc-error> elements from
                #    the response. We've already confirmed they are all warnings
                rsp = etree.fromstring(str(JXML.strip_rpc_error_transform(rsp)))
            else:
                # ignore_warning was false, or an RPCError which doesn't have
                #  an XML attribute. Raise it up for the caller to deal with.
                raise ex
        except Exception as err:
            raise err

        # safety check added in case the rpc-reply for zeroize doesn't have message
        # This scenario is not expected.
        if isinstance(rsp, bool):
            return "zeroize initiated with no message"

        output_msg += "\n".join(
            [i.text for i in rsp.xpath("//message") if i.text is not None]
        )
        return output_msg

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
        fail_list = ["Cannot rollback", "rollback aborted"]
        multi = rsp.xpath("//multi-routing-engine-item")
        if multi:
            rsp = {}
            for x in multi:
                re = x.findtext("re-name")
                output = x.findtext("output")
                if any(x in output for x in fail_list):
                    raise SwRollbackError(re=re, rsp=output)
                else:
                    rsp[re] = output
            return str(rsp)
        else:
            output = rsp.xpath("//output")[0].text
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
        pkgs = fs.ls("/packages")
        return dict(
            current=pkgs["files"].get("junos"), rollback=pkgs["files"].get("junos.old")
        )
