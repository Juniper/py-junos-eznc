from lxml.builder import E

from jnpr.junos.utils.util import Util
from jnpr.junos.utils.start_shell import StartShell

from jnpr.junos.exception import RpcError


class FS(Util):

    """
    Filesystem (FS) utilities:

    * :meth:`cat`: show the contents of a file
    * :meth:`checksum`: calculate file checksum (md5,sha256,sha1)
    * :meth:`cp`: local file copy (not scp)
    * :meth:`cwd`: change working directory
    * :meth:`ls`: return file/dir listing
    * :meth:`mkdir`: create a directory
    * :meth:`pwd`: get working directory
    * :meth:`mv`: local file rename
    * :meth:`rm`: local file delete
    * :meth:`rmdir`: remove a directory
    * :meth:`stat`: return file/dir information
    * :meth:`storage_usage`: return storage usage
    * :meth:`directory_usage`: return directory usage
    * :meth:`storage_cleanup`: perform storage storage_cleanup
    * :meth:`storage_cleanup_check`: returns a list of files which will be
                                     removed at cleanup
    * :meth:`symlink`: create a symlink
    * :meth:`tgz`: tar+gzip a directory

    .. note: The following methods require 'start shell' priveldges:

              * mkdir
              * rmdir
              * symlink
    """

    # -------------------------------------------------------------------------
    # cat - show file contents
    # -------------------------------------------------------------------------

    def cat(self, path):
        """
        Returns the contents of the file **path**.

        :param str path: File-path

        :returns: contents of the file (str) or ``None`` if file does not exist
        """
        try:
            rsp = self._dev.rpc.file_show(filename=path)
        except:
            return None
        return rsp.text

    # -------------------------------------------------------------------------
    # cwd - change working directory
    # -------------------------------------------------------------------------

    def cwd(self, path):
        """
        Change working directory to **path**.

        :param str path: path to working directory
        """
        rsp = self._dev.rpc.set_cli_working_directory(directory=path)
        return rsp.findtext("working-directory")

    # -------------------------------------------------------------------------
    # pwd - return current working directory
    # -------------------------------------------------------------------------

    def pwd(self):
        """
        :returns: The current working directory path (str)
        """
        rsp = self._dev.rpc(E.command("show cli directory"))
        return rsp.findtext("./working-directory")

    # -------------------------------------------------------------------------
    # checksum - compute file checksum
    # -------------------------------------------------------------------------

    def checksum(self, path, calc="md5"):
        """
        Performs the checksum command on the given file path using the
        required calculation method and returns the string value.
        If the **path** is not found on the device, then ``None`` is returned.

        :param str path: file-path on local device
        :param str calc: checksum calculation method:

                         * "md5"
                         * "sha256"
                         * "sha1"

        :returns: checksum value (str) or ``None`` if file not found
        """
        cmd_map = {
            "md5": self._dev.rpc.get_checksum_information,
            "sha256": self._dev.rpc.get_sha256_checksum_information,
            "sha1": self._dev.rpc.get_sha1_checksum_information,
        }
        rpc = cmd_map.get(calc)
        if rpc is None:
            raise ValueError("Unknown calculation method: '%s'" % calc)
        try:
            rsp = rpc(path=path)
            return rsp.findtext(".//checksum").strip()
        except:
            # the only exception is that the path is not found
            return None

    @classmethod
    def _decode_file(cls, fileinfo):
        results = {}

        not_file = fileinfo.xpath("file-directory | file-symlink-target")
        if len(not_file):
            results["type"] = {"file-directory": "dir", "file-symlink-target": "link"}[
                not_file[0].tag
            ]
            if "link" == results["type"]:
                results["link"] = not_file[0].text.strip()
        else:
            results["type"] = "file"

        results["path"] = fileinfo.findtext("file-name").strip()
        results["owner"] = fileinfo.findtext("file-owner").strip()
        results["size"] = int(fileinfo.findtext("file-size"))
        fper = fileinfo.find("file-permissions")
        results["permissions"] = int(fper.text.strip())
        results["permissions_text"] = fper.get("format")
        fdate = fileinfo.find("file-date")
        results["ts_date"] = fdate.get("format")
        results["ts_epoc"] = fdate.text.strip()
        return results

    @classmethod
    def _decode_dir(cls, dirinfo, files=None):
        results = {}
        results["type"] = "dir"
        results["path"] = dirinfo.get("name")
        if files is None:
            files = dirinfo.xpath("file-information")
        results["file_count"] = len(files)
        results["size"] = sum([int(f.findtext("file-size")) for f in files])
        return results

    # -------------------------------------------------------------------------
    # stat - file information
    # -------------------------------------------------------------------------

    def stat(self, path):
        """
        Returns a dictionary of status information on the path, or ``None``
        if the path does not exist.

        :param str path: file-path on local device

        :returns: status information on the file
        :rtype: dict
        """
        rsp = self._dev.rpc.file_list(detail=True, path=path)

        # if there is an output tag, then it means that the path
        # was not found
        if rsp.find("output") is not None:
            return None

        # ok, so we've either got a directory or a file at
        # this point, so decode accordingly

        xdir = rsp.find("directory")
        if xdir.get("name"):  # then this is a directory path
            return FS._decode_dir(xdir)
        else:
            return FS._decode_file(xdir.find("file-information"))

    # -------------------------------------------------------------------------
    # ls - file/dir listing
    # -------------------------------------------------------------------------

    def ls(self, path=".", brief=False, followlink=True):
        """
        File listing, returns a dict of file information.  If the
        path is a symlink, then by default **followlink** will
        recursively call this method to obtain the symlink specific
        information.

        :param str path:
            file-path on local device. defaults to current
            working directory
        :param bool brief:
            when ``True`` brief amount of data
        :param bool followlink:
            when ``True`` (default) this method will recursively
            follow the directory symlinks to gather data

        :returns: dict collection of file information or ``None``
                  if **path** is not found
        """
        rsp = self._dev.rpc.file_list(detail=True, path=path)

        # if there is an output tag, then it means that the path
        # was not found, and we return :None:

        if rsp.find("output") is not None:
            return None

        xdir = rsp.find(".//directory")

        # check to see if the directory element has a :name:
        # attribute, and if it does not, then this is a file, and
        # decode accordingly.  If the file is a symlink, then we
        # want to follow the symlink to get what we want.

        if not xdir.get("name"):
            results = FS._decode_file(xdir.find("file-information"))
            link_path = results.get("link")
            if not link_path:  # then we are done
                return results
            else:
                return results if followlink is False else self.ls(path=link_path)

        # if we are here, then it's a directory, include information on all
        # files
        files = xdir.xpath("file-information")
        results = FS._decode_dir(xdir, files)

        if brief is True:
            results["files"] = [f.findtext("file-name").strip() for f in files]
        else:
            results["files"] = dict(
                (f.findtext("file-name").strip(), FS._decode_file(f)) for f in files
            )

        return results

    # -------------------------------------------------------------------------
    # storage_usage - filesystem storage usage
    # -------------------------------------------------------------------------

    def storage_usage(self):
        """
        Returns the storage usage, similar to the unix "df" command.

        :returns: dict of storage usage
        """
        rsp = self._dev.rpc.get_system_storage()

        def _name(fs):
            return fs.findtext("filesystem-name").strip()

        def _decode(fs):
            r = {}
            r["mount"] = fs.find("mounted-on").text.strip()
            tb = fs.find("total-blocks")
            r["total"] = tb.get("format")
            r["total_blocks"] = int(tb.text)
            ub = fs.find("used-blocks")
            r["used"] = ub.get("format")
            r["used_blocks"] = int(ub.text)
            r["used_pct"] = fs.find("used-percent").text.strip()
            ab = fs.find("available-blocks")
            r["avail"] = ab.get("format")
            r["avail_block"] = int(ab.text)
            return r

        re_list = rsp.xpath("multi-routing-engine-item")
        if re_list:
            fs_dict = {}
            for re in re_list:
                re_name = re.findtext("re-name").strip()
                re_fs_dict = dict(
                    (_name(fs), _decode(fs))
                    for fs in re.xpath("system-storage-information/filesystem")
                )
                fs_dict[re_name] = re_fs_dict
            return fs_dict

        return dict((_name(fs), _decode(fs)) for fs in rsp.xpath("filesystem"))

    # -------------------------------------------------------------------------
    # directory_usage - filesystem directory usage
    # -------------------------------------------------------------------------

    def directory_usage(self, path=".", depth=0):
        """
        Returns the directory usage, similar to the unix "du" command.

        :returns: dict of directory usage, including subdirectories
                  if depth > 0
        """
        BLOCK_SIZE = 512

        rsp = self._dev.rpc.get_directory_usage_information(path=path, depth=str(depth))

        result = {}

        directories = rsp.findall(".//directory")
        if not directories:
            raise RpcError(rsp=rsp)

        for directory in directories:
            dir_name = directory.findtext("directory-name")
            if dir_name is not None:
                dir_name = dir_name.strip()
            else:
                raise RpcError(rsp=rsp)

            used_space = directory.find("used-space")
            if used_space is not None:
                dir_size = used_space.text.strip()
                dir_blocks = used_space.get("used-blocks")
                if dir_blocks is not None:
                    dir_blocks = int(dir_blocks)
                    dir_bytes = dir_blocks * BLOCK_SIZE
                    result[dir_name.strip()] = {
                        "size": dir_size,
                        "blocks": dir_blocks,
                        "bytes": dir_bytes,
                    }

        return result

    # -------------------------------------------------------------------------
    # storage_cleanup_check, storage_cleanip
    # -------------------------------------------------------------------------

    @classmethod
    def _decode_storage_cleanup(cls, files):
        def _name(f):
            return f.findtext("file-name").strip()

        def _decode(f):
            return {
                "size": int(f.findtext("size")),
                "ts_date": f.findtext("date").strip(),
            }

        # return a dict of name/decode pairs for each file
        return dict((_name(f), _decode(f)) for f in files)

    def storage_cleanup_check(self):
        """
        Perform the 'request system storage cleanup dry-run' command
        to return a ``dict`` of files/info that would be removed if
        the cleanup command was executed.

        :returns: dict of files that would be removed (dry-run)
        """
        rsp = self._dev.rpc.request_system_storage_cleanup(dry_run=True)
        files = rsp.xpath("file-list/file")
        return FS._decode_storage_cleanup(files)

    def storage_cleanup(self):
        """
        Perform the 'request system storage cleanup' command to remove
        files from the filesystem.  Return a ``dict`` of file name/info
        on the files that were removed.

        :returns: dict on files that were removed
        """
        rsp = self._dev.rpc.request_system_storage_cleanup()
        files = rsp.xpath("file-list/file")
        return FS._decode_storage_cleanup(files)

    # -------------------------------------------------------------------------
    # rm - local file delete
    # -------------------------------------------------------------------------

    def rm(self, path):
        """
        Performs a local file delete action, per Junos CLI command
        "file delete".

        :returns: ``True`` when successful, ``False`` otherwise.
        """
        # the return value from this RPC will return either True if the delete
        # was successful, or an XML structure otherwise.  So we can do a simple
        # test to provide the return result to the caller.
        rsp = self._dev.rpc.file_delete(path=path)
        if rsp is True:
            return True
        else:
            return False

    # -------------------------------------------------------------------------
    # cp - local file copy
    # -------------------------------------------------------------------------

    def cp(self, from_path, to_path):
        """
        Perform a local file copy where **from_path** and **to_path** can be
        any valid Junos path argument.  Refer to the Junos "file copy" command
        documentation for details.

        :param str from_path: source file-path
        :param str to_path: destination file-path

        .. notes: Valid Junos file-path can include URL, such as ``http://``.
                  this is handy for copying files for webservers.

        :returns: ``True`` if OK, ``False`` if file does not exist.
        """
        # this RPC returns True if it is OK.  If the file does not exist
        # this RPC will generate an RpcError exception, so just return False
        try:
            self._dev.rpc.file_copy(source=from_path, destination=to_path)
        except:
            return False
        return True

    # -------------------------------------------------------------------------
    # mv - local file rename
    # -------------------------------------------------------------------------

    def mv(self, from_path, to_path):
        """
        Perform a local file rename function, same as "file rename" Junos CLI.

        :returns: ``True`` if OK, ``False`` if file does not exist.
        """
        rsp = self._dev.rpc.file_rename(source=from_path, destination=to_path)
        if rsp is True:
            return True
        else:
            return False

    def tgz(self, from_path, tgz_path):
        """
        Create a file called **tgz_path** that is the tar-gzip of the given
        directory specified **from_path**.

        :param str from_path: file-path to directory of files
        :param str tgz_path: file-path name of tgz file to create

        :returns: ``True`` if OK, error-msg (str) otherwise
        """
        rsp = self._dev.rpc.file_archive(
            compress=True, source=from_path, destination=tgz_path
        )

        # if the rsp is True, then the command executed OK.
        if rsp is True:
            return True

        # otherwise, return the error string to the caller
        return rsp.text

    # -------------------------------------------------------------------------
    # !!!!! methods that use SSH shell commands, require that the user
    # !!!!! has 'start shell' privileges
    # -------------------------------------------------------------------------

    def _ssh_exec(self, command):
        with StartShell(self._dev) as sh:
            got = sh.run(command)
        return got

    def rmdir(self, path):
        """
        Executes the 'rmdir' command on **path**.

        .. warning:: REQUIRES SHELL PRIVILEGES

        :param str path: file-path to directory

        :returns: ``True`` if OK, error-message (str) otherwise
        """
        results = self._ssh_exec("rmdir %s" % path)
        return True if results[0] is True else "".join(results[1][2:-1])

    def mkdir(self, path):
        """
        Executes the 'mkdir -p' command on **path**.

        .. warning:: REQUIRES SHELL PRIVILEGES

        :returns: ``True`` if OK, error-message (str) otherwise
        """
        results = self._ssh_exec("mkdir -p %s" % path)
        return True if results[0] is True else "".join(results[1][2:-1])

    def symlink(self, from_path, to_path):
        """
        Executes the 'ln -sf **from_path** **to_path**' command.

        .. warning:: REQUIRES SHELL PRIVILEGES

        :returns: ``True`` if OK, or error-message (str) otherwise
        """
        results = self._ssh_exec("ln -sf %s %s" % (from_path, to_path))
        return True if results[0] is True else "".join(results[1][2:-1])
