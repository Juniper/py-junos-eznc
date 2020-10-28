# utils/config.py
import os
import re
import warnings

# 3rd-party modules
from lxml import etree

# package modules
from jnpr.junos.exception import *
from jnpr.junos import jxml as JXML
from jnpr.junos.utils.util import Util

"""
Configuration Utilities
"""


class Config(Util):
    """
    Overview of Configuration Utilities.

    * :meth:`commit`: commit changes
    * :meth:`commit_check`: perform the commit check operation
    * :meth:`diff`: return the diff string between running and candidate config
    * :meth:`load`: load changes into the candidate config
    * :meth:`lock`: take an exclusive lock on the candidate config
    * :meth:`pdiff`: prints the diff string (debug/helper)
    * :meth:`rescue`: controls "rescue configuration"
    * :meth:`rollback`: perform the load rollback command
    * :meth:`unlock`: release the exclusive lock
    """

    # ------------------------------------------------------------------------
    # commit
    # ------------------------------------------------------------------------
    def commit(self, **kvargs):
        """
        Commit a configuration.

        :param str comment: If provided logs this comment with the commit.
        :param int confirm: If provided activates confirm safeguard with
                            provided value as timeout (minutes).
        :param int timeout: If provided the command will wait for completion
                            using the provided value as timeout (seconds).
                            By default the device timeout is used.
        :param bool sync: On dual control plane systems, requests that
                            the candidate configuration on one control plane be
                            copied to the other control plane, checked for
                            correct syntax, and committed on both Routing
                            Engines.
        :param bool force_sync: On dual control plane systems, forces the
                            candidate configuration on one control plane to
                            be copied to the other control plane.
        :param bool full: When true requires all the daemons to check and
                            evaluate the new configuration.
        :param bool detail: When true return commit detail as XML

        :param ignore_warning: A boolean, string or list of string.
          If the value is True, it will ignore all warnings regardless of the
          warning message. If the value is a string, it will ignore
          warning(s) if the message of each warning matches the string. If
          the value is a list of strings, ignore warning(s) if the message of
          each warning matches at least one of the strings in the list.

          For example::

            cu.commit(ignore_warning=True)
            cu.commit(ignore_warning='Advertisement-interval is '
                                     'less than four times')
            cu.commit(ignore_warning=['Advertisement-interval is '
                                      'less than four times',
                                      'Chassis configuration for network '
                                      'services has been changed.'])

          .. note::
            When the value of ignore_warning is a string, or list of strings,
            the string is actually used as a case-insensitive regular
            expression pattern. If the string contains only alpha-numeric
            characters, as shown in the above examples, this results in a
            case-insensitive substring match. However, any regular expression
            pattern supported by the re library may be used for more
            complicated match conditions.

        :returns:
            * ``True`` when successful
            * Commit detail XML (when detail is True)

        :raises CommitError: When errors detected in candidate configuration.
                             You can use the Exception errs variable
                             to identify the specific problems

        .. warning::
            If the function does not receive a reply prior to the timeout
            a RpcTimeoutError will be raised.  It is possible the commit
            was successful.  Manual verification may be required.
        """
        rpc_args = {}

        # if a comment is provided, then include that in the RPC

        comment = kvargs.get("comment")
        if comment:
            rpc_args["log"] = comment

        # if confirm is provided, then setup the RPC args
        # so that Junos will either use the default confirm
        # timeout (confirm=True) or a specific timeout
        # (confirm=<minutes>)

        confirm = kvargs.get("confirm")
        if confirm:
            rpc_args["confirmed"] = True
            confirm_val = str(confirm)
            if "True" != confirm_val:
                rpc_args["confirm-timeout"] = confirm_val

        # if a timeout is provided, then include that in the RPC

        timeout = kvargs.get("timeout")
        if timeout:
            rpc_args["dev_timeout"] = timeout

        # Check for force_sync and sync
        if kvargs.get("force_sync"):
            rpc_args["synchronize"] = True
            rpc_args["force-synchronize"] = True
        elif kvargs.get("sync"):
            rpc_args["synchronize"] = True

        # Check for full
        if kvargs.get("full"):
            rpc_args["full"] = True

        # Check for ignore_warning
        ignore_warn = kvargs.get("ignore_warning")
        if ignore_warn:
            rpc_args["ignore_warning"] = ignore_warn

        rpc_varg = []
        detail = kvargs.get("detail")
        if detail:
            rpc_varg = [{"detail": "detail"}]

        # dbl-splat the rpc_args since we want to pass key/value to metaexec
        # if there is a commit/check error, this will raise an execption

        try:
            rsp = self.rpc.commit_configuration(*rpc_varg, **rpc_args)
        except RpcTimeoutError:
            raise
        except RpcError as err:  # jnpr.junos exception
            if err.rsp is not None and err.rsp.find("ok") is not None:
                # this means there are warnings, but no errors
                return True
            else:
                raise CommitError(cmd=err.cmd, rsp=err.rsp, errs=err.errs)
        except Exception as err:
            # so the ncclient gives us something I don't want.  I'm going to
            # convert it and re-raise the commit error
            if hasattr(err, "xml") and isinstance(err.xml, etree._Element):
                raise CommitError(rsp=err.xml)
            else:
                raise

        if detail:
            return rsp
        else:
            return True

    # -------------------------------------------------------------------------
    # commit check
    # -------------------------------------------------------------------------

    def commit_check(self, **kvargs):
        """
        Perform a commit check.  If the commit check passes, this function
        will return ``True``.  If the commit-check results in warnings, they
        are reported and available in the Exception errs.

        :param int timeout: If provided the command will wait for completion
                            using the provided value as timeout (seconds).

        :returns: ``True`` if commit-check is successful (no errors)
        :raises CommitError: When errors detected in candidate configuration.
                             You can use the Exception errs variable
                             to identify the specific problems
        :raises RpcError: When underlying ncclient has an error
        """
        rpc_args = {}

        # if a timeout is provided, then include that in the RPC

        timeout = kvargs.get("timeout")
        if timeout:
            rpc_args["dev_timeout"] = timeout

        try:
            self.rpc.commit_configuration(check=True, **rpc_args)
        except RpcTimeoutError:
            raise
        except RpcError as err:  # jnpr.junos exception
            if err.rsp is not None and err.rsp.find("ok") is not None:
                # this means there is a warning, but no errors
                return True
            else:
                raise CommitError(cmd=err.cmd, rsp=err.rsp, errs=err.errs)
        except Exception as err:
            # :err: is from ncclient, so extract the XML data
            # and convert into dictionary
            if hasattr(err, "xml") and isinstance(err.xml, etree._Element):
                return JXML.rpc_error(err.xml)
            else:
                raise

        return True

    # -------------------------------------------------------------------------
    # show | compare rollback <number|0*>
    # -------------------------------------------------------------------------

    def diff(self, rb_id=0, ignore_warning=False, use_fast_diff=False):
        """
        Retrieve a diff (patch-format) report of the candidate config against
        either the current active config, or a different rollback.

        :param int rb_id: rollback id [0..49]
        :param bool ignore_warning: Ignore any rpc-error with severity warning
        :param bool use_fast_diff: equivalent to "show | compare use-fast-diff"

        :returns:
            * ``None`` if there is no difference
            * ascii-text (str) if there is a difference
        """

        if rb_id < 0 or rb_id > 49:
            raise ValueError("Invalid rollback #" + str(rb_id))

        rpc_params = dict(compare="rollback", rollback=str(rb_id), format="text")
        if use_fast_diff:
            if rb_id > 0:
                raise ValueError("use_fast_diff can only be used with rb_id 0")
            rpc_params["use-fast-diff"] = "yes"
        try:
            rsp = self.rpc.get_configuration(
                rpc_params,
                ignore_warning=ignore_warning,
            )
        except RpcTimeoutError:
            raise
        except RpcError as err:
            if (
                err.rpc_error["severity"] == "warning"
                and err.message == "mgd: statement must contain additional "
                "statements"
            ):
                # Fix for Issue #655, JDM 15.1X53-D45 responses with
                # extraneous warning message
                return "Unable to parse diff from response!"
            else:
                raise

        diff_txt = rsp.find("configuration-output").text
        return None if diff_txt == "\n" else diff_txt

    def pdiff(self, rb_id=0, ignore_warning=False, use_fast_diff=False):
        """
        Helper method that calls ``print`` on the diff (patch-format) between
        the current candidate and the provided rollback.

        :param int rb_id: the rollback id value [0-49]
        :param bool ignore_warning: Ignore any rpc-error with severity warning
        :param bool use_fast_diff: equivalent to "show | compare use-fast-diff"

        :returns: ``None``
        """
        print(self.diff(rb_id, ignore_warning, use_fast_diff))

    # -------------------------------------------------------------------------
    # helper on loading configs
    # -------------------------------------------------------------------------

    def load(self, *vargs, **kvargs):
        """
        Loads changes into the candidate configuration.  Changes can be
        in the form of strings (text,set,xml, json), XML objects, and files.
        Files can be either static snippets of configuration or Jinja2
        templates.  When using Jinja2 Templates, this method will render
        variables into the templates and then load the resulting change;
        i.e. "template building".

        :param object vargs[0]:
            The content to load.  If the contents is a string, the framework
            will attempt to automatically determine the format.  If it is
            unable to determine the format then you must specify the
            **format** parameter.  If the content is an XML object, then
            this method assumes you've structured it correctly;
            and if not an Exception will be raised.

        :param str path:
            Path to file of configuration on the local server.
            The path extension will be used to determine the format of
            the contents:

            * "conf","text","txt" is curly-text-style
            * "set" - ascii-text, set-style
            * "xml" - ascii-text, XML
            * "json" - ascii-text, json

            .. note:: The format can specifically set using **format**.

        :param str format:
            Determines the format of the contents.
            Supported options - text, set, xml, json

            If not provided, internally application will try to find out the format

        :param bool overwrite:
          Determines if the contents completely replace the existing
          configuration.  Default is ``False``.

          .. note:: This option cannot be used if **format** is "set".

        :param bool merge:
          If set to ``True`` will set the load-config action to merge.
          the default load-config action is 'replace'

        :param bool update:
          If set to ``True`` Compare a complete loaded configuration against
          the candidate configuration. For each hierarchy level or
          configuration object that is different in the two configurations,
          the version in the loaded configuration replaces the version in the
          candidate configuration. When the configuration is later committed,
          only system processes that are affected by the changed configuration
          elements parse the new configuration.

          .. note:: This option cannot be used if **format** is "set".

        :param bool patch:
          If set to ``True`` will set the load-config action to load patch.

        :param str template_path:
          Similar to the **path** parameter, but this indicates that
          the file contents are ``Jinja2`` format and will require
          template-rendering.

          .. note:: This parameter is used in conjunction with
                    **template_vars**. The template filename extension will
                    be used to determine the format-style of the contents,
                    or you can override using **format**.

        :param jinja2.Template template:
          A Jinja2 Template object.  Same description as *template_path*,
          except this option you provide the actual Template, rather than
          a path to the template file.

        :param dict template_vars:
          Used in conjunction with the other template options.  This parameter
          contains a dictionary of variables to render into the template.

        :param ignore_warning: A boolean, string or list of string.
          If the value is True, it will ignore all warnings regardless of the
          warning message. If the value is a string, it will ignore
          warning(s) if the message of each warning matches the string. If
          the value is a list of strings, ignore warning(s) if the message of
          each warning matches at least one of the strings in the list.

          For example::

            cu.load(cnf, ignore_warning=True)
            cu.load(cnf, ignore_warning='statement not found')
            cu.load(cnf, ignore_warning=['statement not found',
                                         'statement has no contents; ignored')

          .. note::
            When the value of ignore_warning is a string, or list of strings,
            the string is actually used as a case-insensitive regular
            expression pattern. If the string contains only alpha-numeric
            characters, as shown in the above examples, this results in a
            case-insensitive substring match. However, any regular expression
            pattern supported by the re library may be used for more
            complicated match conditions.

        :param str url:
          Specify the full pathname of the file that contains the configuration
          data to load. The value can be a local file path, an FTP location, or
          a Hypertext Transfer Protocol (HTTP).
          Refer `Doc page <https://www.juniper.net/documentation/en_US/junos/topics/reference/tag-summary/junos-xml-protocol-load-configuration.html>`_
          for more details.

          For example::

            cu.load(url="/var/home/user/golden.conf")
            cu.load(url="ftp://username@ftp.hostname.net/filename")
            cu.load(url="http://username:password@hostname/path/filename")
            cu.load(url="/var/home/user/golden.conf", overwrite=True)

        :returns:
            RPC-reply as XML object.

        :raises: ConfigLoadError: When errors detected while loading candidate
                                  configuration. You can use the Exception
                                  errs variable  to identify the specific
                                  problems.
        """
        rpc_xattrs = {}
        rpc_xattrs["format"] = "xml"  # default to XML format
        rpc_xattrs["action"] = "replace"  # replace is default action

        rpc_contents = None

        actions = filter(
            lambda item: kvargs.get(item, False),
            ("overwrite", "merge", "update", "patch"),
        )
        if len(list(actions)) >= 2:
            raise ValueError("actions can be only one among %s" % ", ".join(actions))

        # support the ability to completely replace the Junos configuration
        # note: this cannot be used if format='set', per Junos API.

        overwrite = kvargs.get("overwrite", False)
        if overwrite is True:
            rpc_xattrs["action"] = "override"
        if kvargs.get("update") is True:
            rpc_xattrs["action"] = "update"
        elif kvargs.get("merge") is True:
            del rpc_xattrs["action"]
        elif kvargs.get("patch") is True:
            rpc_xattrs["action"] = "patch"

        ignore_warning = kvargs.get("ignore_warning", False)

        # ---------------------------------------------------------------------
        # private helpers ...
        # ---------------------------------------------------------------------

        def _lformat_byext(path):
            """ determine the format style from the file extension """
            ext = os.path.splitext(path)[1]
            if ext == ".xml":
                return "xml"
            if ext in [".conf", ".text", ".txt"]:
                return "text"
            if ext in [".set"]:
                return "set"
            if ext in [".json"]:
                return "json"
            raise ValueError("Unknown file contents from extension: %s" % ext)

        def _lset_format(kvargs, rpc_xattrs):
            """ setup the kvargs/rpc_xattrs """
            # when format is given, setup the xml attrs appropriately
            if kvargs["format"] == "set":
                if overwrite is True or kvargs.get("update") is True:
                    raise ValueError(
                        "conflicting args, cannot use 'set' with '%s'"
                        % ("overwrite" if overwrite is True else "update")
                    )
                rpc_xattrs["action"] = "set"
                kvargs["format"] = "text"
            rpc_xattrs["format"] = kvargs["format"]

        def _lset_fromfile(path):
            """ setup the kvargs/rpc_xattrs based on path """
            if "format" not in kvargs:
                # we use the extension to determine the format
                kvargs["format"] = _lformat_byext(path)
                _lset_format(kvargs, rpc_xattrs)

        def _lset_from_rexp(rpc):
            """ setup the kvargs/rpc_xattrs using string regular expression """
            if re.search(r"^\s*<.*>$", rpc, re.MULTILINE):
                kvargs["format"] = "xml"
            elif re.search(
                r"^\s*(set|delete|rename|insert|activate|deactivate"
                "|annotate|copy|protect|unprotect)\s",
                rpc,
            ):
                kvargs["format"] = "set"
            elif re.search(r"^[a-z:]*\s*[\w-]+\s+\{", rpc, re.I) and re.search(
                r".*}\s*$", rpc
            ):
                kvargs["format"] = "text"
            elif re.search(r"^\s*\{", rpc) and re.search(r".*}\s*$", rpc):
                kvargs["format"] = "json"

        def try_load(rpc_contents, rpc_xattrs, ignore_warning=False):
            try:
                got = self.rpc.load_config(
                    rpc_contents, ignore_warning=ignore_warning, **rpc_xattrs
                )
            except RpcTimeoutError as err:
                raise err
            except RpcError as err:
                raise ConfigLoadError(cmd=err.cmd, rsp=err.rsp, errs=err.errs)
            # Something unexpected happened - raise it up
            except Exception as err:
                raise

            return got

        # ---------------------------------------------------------------------
        # end-of: private helpers
        # ---------------------------------------------------------------------

        if "format" in kvargs:
            _lset_format(kvargs, rpc_xattrs)

        # ---------------------------------------------------------------------
        # if contents are provided as vargs[0], then process that as XML or str
        # ---------------------------------------------------------------------

        if len(vargs):
            # caller is providing the content directly.
            rpc_contents = vargs[0]
            if isinstance(rpc_contents, str):
                if "format" not in kvargs:
                    _lset_from_rexp(rpc_contents)
                    if "format" in kvargs:
                        _lset_format(kvargs, rpc_xattrs)
                    else:
                        raise RuntimeError(
                            "Not able to resolve the config format "
                            "You must define the format of the contents "
                            "explicitly to the function. Ex: format='set'"
                        )
                if kvargs["format"] == "xml":
                    # covert the XML string into XML structure
                    rpc_contents = etree.XML(rpc_contents)

        # ---------------------------------------------------------------------
        # if path is provided, use the static-config file
        # ---------------------------------------------------------------------

        elif "path" in kvargs:
            # then this is a static-config file.  load that as our rpc_contents
            try:
                # Explicitly request Python 3.x universal newline
                rpc_contents = open(kvargs["path"], "r", newline=None).read()
            except TypeError:
                # Fallback to Python 2.x universal newline
                rpc_contents = open(kvargs["path"], "rU").read()
            _lset_fromfile(kvargs["path"])
            if rpc_xattrs["format"] == "xml":
                # covert the XML string into XML structure
                rpc_contents = etree.XML(rpc_contents)

        # ---------------------------------------------------------------------
        # if template_path is provided, then jinja2 load the template, and
        # render the results.  if template_vars are provided, use those
        # in the render process.
        # ---------------------------------------------------------------------

        elif "template_path" in kvargs:
            path = kvargs["template_path"]
            template = self.dev.Template(path)
            rpc_contents = template.render(kvargs.get("template_vars", {}))
            _lset_fromfile(path)
            if rpc_xattrs["format"] == "xml":
                # covert the XML string into XML structure
                rpc_contents = etree.XML(rpc_contents)

        # ---------------------------------------------------------------------
        # if template is provided, then this is a pre-loaded jinja2 Template
        # object.  Use the template.filename to determine the format style
        # ---------------------------------------------------------------------

        elif "template" in kvargs:
            template = kvargs["template"]
            path = template.filename
            rpc_contents = template.render(kvargs.get("template_vars", {}))
            _lset_fromfile(path)
            if rpc_xattrs["format"] == "xml":
                # covert the XML string into XML structure
                rpc_contents = etree.XML(rpc_contents)

        if rpc_contents is not None:
            return try_load(rpc_contents, rpc_xattrs, ignore_warning=ignore_warning)
        elif "url" in kvargs and rpc_contents is None:
            url = kvargs["url"]
            _lset_fromfile(url)
            rpc_xattrs["url"] = url
            return try_load(rpc_contents, rpc_xattrs, ignore_warning=ignore_warning)
        else:
            raise RuntimeError("Unhandled load request")

    # -------------------------------------------------------------------------
    # config exclusive
    # -------------------------------------------------------------------------

    def lock(self):
        """
        Attempts an exclusive lock on the candidate configuration.  This
        is a non-blocking call.

        :returns:
            ``True`` always when successful

        :raises LockError: When the lock cannot be obtained
        """
        try:
            self.rpc.lock_configuration()
        except Exception as err:
            if isinstance(err, RpcError):
                raise LockError(rsp=err.rsp)
            elif isinstance(err, ConnectClosedError):
                raise err
            else:
                # :err: is from ncclient
                raise LockError(rsp=JXML.remove_namespaces(err.xml))

        return True

    # -------------------------------------------------------------------------
    # releases the exclusive lock
    # -------------------------------------------------------------------------

    def unlock(self):
        """
        Unlocks the candidate configuration.

        :returns:
            ``True`` always when successful

        :raises UnlockError: If you attempt to unlock a configuration
                             when you do not own the lock
        """
        try:
            self.rpc.unlock_configuration()
        except Exception as err:
            if isinstance(err, RpcError):
                raise UnlockError(rsp=err.rsp)
            elif isinstance(err, ConnectClosedError):
                raise err
            else:
                # :err: is from ncclient
                raise UnlockError(rsp=JXML.remove_namespaces(err.xml))

        return True

    # -------------------------------------------------------------------------
    # rollback <number|0*>
    # -------------------------------------------------------------------------

    def rollback(self, rb_id=0):
        """
        Rollback the candidate config to either the last active or
        a specific rollback number.

        :param int rb_id: The rollback id value [0-49], defaults to ``0``.

        :returns:
            ``True`` always when successful

        :raises ValueError: When invalid rollback id is given
        """

        if rb_id < 0 or rb_id > 49:
            raise ValueError("Invalid rollback #" + str(rb_id))

        self.rpc.load_configuration(dict(compare="rollback", rollback=str(rb_id)))

        return True

    # -------------------------------------------------------------------------
    # rescue configuration
    # -------------------------------------------------------------------------

    def rescue(self, action, format="text"):
        """
        Perform action on the "rescue configuration".

        :param str action: identifies the action as follows:

            * "get" - retrieves/returns the rescue configuration via **format**
            * "save" - saves current configuration as rescue
            * "delete" - removes the rescue configuration
            * "reload" - loads the rescue config as candidate (no-commit)

        :param str format: identifies the return format when **action** is
                           "get":

            * "text" (default) - ascii-text format
            * "xml" - as XML object

        :return:

            * When **action** is 'get', then the contents of the rescue
              configuration is returned in the specified *format*.  If there
              is no rescue configuration saved, then the return value is
              ``None``.

            * ``True`` when **action** is "save".

            * ``True`` when **action** is "delete".

            .. note:: ``True`` regardless if a rescue configuration exists.

            * When **action** is 'reload', return is ``True`` if a rescue
              configuration exists, and ``False`` otherwise.

            .. note:: The rescue configuration is only loaded as the candidate,
                      and not committed.  You must commit to make the rescue
                      configuration active.

        :raises ValueError:
            If **action** is not one of the above
        """

        def _rescue_save():
            """
            Saves the current configuration as the rescue configuration
            """
            self.rpc.request_save_rescue_configuration()
            return True

        def _rescue_delete():
            """
            Deletes the existing resuce configuration.
            """
            # note that this will result in an "OK" regardless if
            # a rescue config exists or not.
            self.rpc.request_delete_rescue_configuration()
            return True

        def _rescue_get():
            """
            Retrieves the rescue configuration, returning it in
            either :format: 'text' or 'xml'.

            Returns either the 'text'/'xml' if the rescue config
            exists, or :None: otherwise
            """
            try:
                got = self.rpc.get_rescue_information(format=format)
                return (
                    got.findtext("configuration-information/configuration-output")
                    if "text" == format
                    else got
                )
            except:
                return None

        def _rescue_reload():
            """
            Loads the rescue configuration as the active candidate.
            This action does *not* commit the configuration; use the
            :commit(): method for that purpose.

            Returns the XML response if the rescue configuration
            exists, or :False: otherwise
            """
            try:
                return self.rpc.load_configuration({"rescue": "rescue"})
            except:
                return False

        def _unsupported_action():
            raise ValueError("unsupported action: {}".format(action))

        result = {
            "get": _rescue_get,
            "save": _rescue_save,
            "delete": _rescue_delete,
            "reload": _rescue_reload,
        }.get(action, _unsupported_action)()

        return result

    def __init__(self, dev, mode=None, **kwargs):
        """
        :param str mode: Can be used *only* when creating Config object using
                         context manager

            * "private" - Work in private database
            * "dynamic" - Work in dynamic database
            * "batch" - Work in batch database
            * "exclusive" - Work with Locking the candidate configuration
            * "ephemeral" - Work in default/specified ephemeral instance

        :param str ephemeral_instance: ephemeral instance name

        .. code-block:: python

           # mode can be private/dynamic/exclusive/batch/ephemeral
           with Config(dev, mode='exclusive') as cu:
               cu.load('set system services netconf traceoptions file xyz',
                       format='set')
               print cu.diff()
               cu.commit()

        .. warning::
            Ephemeral databases are an advanced Junos feature which
            if used incorrectly can have serious negative impact on the operation
            of the Junos device. We recommend you consult JTAC and/or you Juniper
            account team before deploying the ephemeral database feature in your
            network.
        """
        self.mode = mode
        if not kwargs.get("ephemeral_instance") and kwargs:
            raise ValueError("Unsupported argument provided to Config class")
        self.kwargs = kwargs

        Util.__init__(self, dev=dev)

    def __enter__(self):

        # defining separate functions for each mode so that can be
        # changed/edited as per the need of corresponding rpc call.
        def _open_configuration_private():
            try:
                self.rpc.open_configuration(private=True)
            except (RpcTimeoutError, ConnectClosedError) as err:
                raise err
            except RpcError as err:
                if err.rpc_error["severity"] == "warning":
                    if (
                        err.message != "uncommitted changes will be discarded "
                        "on exit"
                    ):
                        warnings.warn(err.message, RuntimeWarning)
                    return True
                else:
                    raise err

        def _open_configuration_dynamic():
            try:
                self.rpc.open_configuration(dynamic=True)
            except RpcError as err:
                raise err
            return True

        def _open_configuration_batch():
            try:
                self.rpc.open_configuration(batch=True)
            except (RpcTimeoutError, ConnectClosedError) as err:
                raise err
            except RpcError as err:
                if err.rpc_error["severity"] == "warning":
                    if (
                        err.message != "uncommitted changes will be discarded "
                        "on exit"
                    ):
                        warnings.warn(err.message, RuntimeWarning)
                    return True
                else:
                    raise err

        def _open_configuration_exclusive():
            return self.lock()

        def _open_configuration_ephemeral(**kwargs):
            self.rpc.open_configuration(**kwargs)
            return True

        def _unsupported_option():
            if self.mode is not None:
                raise ValueError("unsupported action: {}".format(self.mode))

        if self.kwargs.get("ephemeral_instance"):
            ephemeral_kwargs = {"ephemeral_instance": self.kwargs["ephemeral_instance"]}
        else:
            ephemeral_kwargs = {"ephemeral": True}

        {
            "private": _open_configuration_private,
            "dynamic": _open_configuration_dynamic,
            "batch": _open_configuration_batch,
            "exclusive": _open_configuration_exclusive,
            "ephemeral": lambda: _open_configuration_ephemeral(**ephemeral_kwargs),
        }.get(self.mode, _unsupported_option)()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.mode == "exclusive":
            self.unlock()
        elif self.mode is not None:
            self.rpc.close_configuration()
