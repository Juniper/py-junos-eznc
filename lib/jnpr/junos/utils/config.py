# utils/config.py
import os

# 3rd-party modules
from lxml import etree

# package modules
from jnpr.junos.exception import *
from jnpr.junos import jxml as JXML
from jnpr.junos.utils.util import Util


class Config(Util):

    """
    Configuration Utilities:

      commit - commit changes
      commit_check - perform the commit check operation
      diff - return the diff string between running and candidate config
      pdiff - prints the diff string (debug/helper)
      load - load changes into the candidate config
      lock - take an exclusive lock on the candidate config
      unlock - release the exclusive lock
      rollback - perform the load rollback command

    """

    # ------------------------------------------------------------------------
    # commit
    # ------------------------------------------------------------------------

    def commit(self, **kvargs):
        """
        commit a configuration.  returns either :True: or
        raises an RPCError exception

        kvargs
          confirm = [True | <timeout-minutes>]
          comment = <comment log string>
        """
        rpc_args = {}

        # if a comment is provided, then include that in the RPC

        comment = kvargs.get('comment')
        if comment:
            rpc_args['log'] = comment

        # if confirm is provided, then setup the RPC args
        # so that Junos will either use the default confirm
        # timeout (confirm=True) or a specific timeout
        # (confirm=<minutes>)

        confirm = kvargs.get('confirm')
        if confirm:
            rpc_args['confirmed'] = True
            confirm_val = str(confirm)
            if 'True' != confirm_val:
                rpc_args['confirm-timeout'] = confirm_val

        # dbl-splat the rpc_args since we want to pass key/value to metaexec
        # if there is a commit/check error, this will raise an execption

        try:
            self.rpc.commit_configuration(**rpc_args)
        except RpcError as err:        # jnpr.junos exception
            if err.rsp.find('ok') is not None:
                # this means there are warnings, but no errors
                return True
            else:
                raise CommitError(cmd=err.cmd, rsp=err.rsp)
        except Exception as err:
            # so the ncclient gives us something I don't want.  I'm going to
            # convert it and re-raise the commit error
            JXML.remove_namespaces(err.xml)
            raise CommitError(rsp=err.xml)

        return True

    # -------------------------------------------------------------------------
    # commit check
    # -------------------------------------------------------------------------

    def commit_check(self):
        """
        perform a commit check.  if the commit check passes, this function
        will return :True:

        If there is a commit check error, then the RPC error reply XML
        structure will be returned
        """
        try:
            self.rpc.commit_configuration(check=True)
        except RpcError as err:        # jnpr.junos exception
            if err.rsp.find('ok') is not None:
                # this means there is a warning, but no errors
                return True
            else:
                raise CommitError(cmd=err.cmd, rsp=err.rsp)
        except Exception as err:
            # :err: is from ncclient, so extract the XML data
            # and convert into dictionary
            return JXML.rpc_error(err.xml)

        return True

    # -------------------------------------------------------------------------
    # show | compare rollback <number|0*>
    # -------------------------------------------------------------------------

    def diff(self, **kvargs):
        """
        retrieve a diff-format report of the candidate config against
        either the current active config, or a different rollback.

        kvargs
          'rollback' is a number [0..50]
        """

        rb_id = kvargs.get('rollback', 0)
        if rb_id < 0 or rb_id > 50:
            raise ValueError("Invalid rollback #" + str(rb_id))

        rsp = self.rpc.get_configuration(dict(
            compare='rollback', rollback=str(rb_id), format='text'
        ))

        diff_txt = rsp.find('configuration-output').text
        return None if diff_txt == "\n" else diff_txt

    def pdiff(self, **kvargs):
        print self.diff(**kvargs)

    # -------------------------------------------------------------------------
    # helper on loading configs
    # -------------------------------------------------------------------------

    def load(self, *vargs, **kvargs):
        """
        loads configuration into the device

        vargs (optional)
          is the content to load.  if the contents is a string, then you
          must specify kvargs['format'].

        kvargs['path']
            path to file of configuration.  the path extension will be used
            to determine the format of the contents.

                | ['conf','text','txt'] is curly-text-style
                | ['set'] is set-style
                | ['xml'] is XML

            the format can specific set by using kvarg['format']

        kvargs['format']
          determines the format of the contents.  options are
          ['xml','set','text'] for XML/etree, set-style, curly-brace-style

        kvargs['overwrite']
          determines if the contents completely replace the existing
          configuration.  options are [True/False], default: False

        kvargs['template_path']
          path to a jinja2 template file.  used in conjection with the
          kvargs['template_vars'] option, this will perform a templating
          render and then load the result.  The template extension will
          be used to determine the format-style of the contents, or you
          can override using kvargs['format']

        kvargs['template']
          jinja2 Template.  same description as kvargs['template_path'],
          except this option you provide the actual Template, rather than
          a path to the template file

        kvargs['template_vars']
          used in conjection with the other template options.  this option
          contains a dictionary of variables to render into the template
        """
        rpc_xattrs = {'format': 'xml'}      # junos attributes, default to XML
        rpc_contents = None

        # support the ability to completely replace the Junos configuration
        # note: this cannot be used if format='set', per Junos API.

        overwrite = kvargs.get('overwrite', False)
        if True == overwrite:
            rpc_xattrs['action'] = 'override'

        # ---------------------------------------------------------------------
        # private helpers ...
        # ---------------------------------------------------------------------

        def _lformat_byext(path):
            """ determine the format style from the file extension """
            ext = os.path.splitext(path)[1]
            if ext == '.xml':
                return 'xml'
            if ext in ['.conf', '.text', '.txt']:
                return 'text'
            if ext in ['.set']:
                return 'set'
            raise ValueError("Unknown file contents from extension: %s" % ext)

        def _lset_format(kvargs, rpc_xattrs):
            """ setup the kvargs/rpc_xattrs """
            # when format is given, setup the xml attrs appropriately
            if kvargs['format'] == 'set':
                if True == overwrite:
                    raise ValueError(
                        "conflicting args, cannot use 'set' with 'overwrite'")
                rpc_xattrs['action'] = 'set'
                kvargs['format'] = 'text'
            rpc_xattrs['format'] = kvargs['format']

        def _lset_fromfile(path):
            """ setup the kvargs/rpc_xattrs based on path """
            if 'format' not in kvargs:
                # we use the extension to determine the format
                kvargs['format'] = _lformat_byext(path)
                _lset_format(kvargs, rpc_xattrs)

        # ---------------------------------------------------------------------
        # end-of: private helpers
        # ---------------------------------------------------------------------

        if 'format' in kvargs:
            _lset_format(kvargs, rpc_xattrs)

        # ---------------------------------------------------------------------
        # if contents are provided as vargs[0], then process that as XML or str
        # ---------------------------------------------------------------------

        if len(vargs):
            # caller is providing the content directly.
            rpc_contents = vargs[0]
            if isinstance(rpc_contents, str) and not 'format' in kvargs:
                raise RuntimeError(
                    "You must define the format of the contents")
            return self.rpc.load_config(rpc_contents, **rpc_xattrs)

            #~! UNREACHABLE !~#

        # ---------------------------------------------------------------------
        # if path is provided, use the static-config file
        # ---------------------------------------------------------------------

        if 'path' in kvargs:
            # then this is a static-config file.  load that as our rpc_contents
            rpc_contents = open(kvargs['path'], 'rU').read()
            _lset_fromfile(kvargs['path'])
            if rpc_xattrs['format'] == 'xml':
                # covert the XML string into XML structure
                rpc_contents = etree.XML(rpc_contents)

            return self.rpc.load_config(rpc_contents, **rpc_xattrs)

            #~! UNREACHABLE !~#

        # ---------------------------------------------------------------------
        # if template_path is provided, then jinja2 load the template, and
        # render the results.  if template_vars are provided, use those
        # in the render process.
        # ---------------------------------------------------------------------

        if 'template_path' in kvargs:
            path = kvargs['template_path']
            template = self.dev.Template(path)
            rpc_contents = template.render(kvargs.get('template_vars', {}))
            _lset_fromfile(path)
            return self.rpc.load_config(rpc_contents, **rpc_xattrs)

            #~! UNREACHABLE !~#

        # ---------------------------------------------------------------------
        # if template is provided, then this is a pre-loaded jinja2 Template
        # object.  Use the template.filename to determine the format style
        # ---------------------------------------------------------------------

        if 'template' in kvargs:
            template = kvargs['template']
            path = template.filename
            rpc_contents = template.render(kvargs.get('template_vars', {}))
            _lset_fromfile(path)
            return self.rpc.load_config(rpc_contents, **rpc_xattrs)

            #~! UNREACHABLE !~#

        raise RuntimeError("Unhandled load request")

    # -------------------------------------------------------------------------
    # config exclusive
    # -------------------------------------------------------------------------

    def lock(self):
        """
        attempts an exclusive lock on the candidate configuration
        """
        try:
            self.rpc.lock_configuration()
        except Exception as err:
            if isinstance(err, RpcError):
                raise LockError(rsp=err.rsp)
            else:
                # :err: is from ncclient
                raise LockError(rsp=JXML.remove_namespaces(err.xml))

        return True

    # -------------------------------------------------------------------------
    # releases the exclusive lock
    # -------------------------------------------------------------------------

    def unlock(self):
        """
        unlocks the candidate configuration
        """
        try:
            self.rpc.unlock_configuration()
        except Exception as err:
            if isinstance(err, RpcError):
                raise LockError(rsp=err.rsp)
            else:
            # :err: is from ncclient
                raise UnlockError(rsp=JXML.remove_namespaces(err.xml))

        return True

    # -------------------------------------------------------------------------
    # rollback <number|0*>
    # -------------------------------------------------------------------------

    def rollback(self, rb_id=0):
        """
        rollback the candidate config to either the last active or
        a specific rollback number.
        """

        if rb_id < 0 or rb_id > 50:
            raise ValueError("Invalid rollback #" + str(rb_id))

        self.rpc.load_configuration(dict(
            compare='rollback', rollback=str(rb_id)
        ))

        return True
