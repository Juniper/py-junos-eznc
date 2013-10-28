# utils/config.py

# package modules
from ..exception import *
from .. import jxml as JXML

class ConfigUtils(object):

  def __init__(self, junos):
    self._junos = junos

  ### ---------------------------------------------------------------------------
  ### commit
  ### ---------------------------------------------------------------------------

  def commit( self, **kvargs ):
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
    if comment: rpc_args['log'] = comment

    # if confirm is provided, then setup the RPC args
    # so that Junos will either use the default confirm
    # timeout (confirm=True) or a specific timeout
    # (confirm=<minutes>)

    confirm = kvargs.get('confirm')
    if confirm:
      rpc_args['confirmed'] = True
      confirm_val = str(confirm)
      if 'True' != confirm_val: rpc_args['confirm-timeout'] = confirm_val

    # dbl-splat the rpc_args since we want to pass key/value to metaexec
    # if there is a commit/check error, this will raise an execption

    try:
      self._junos.rpc.commit_configuration( **rpc_args )
    except Exception as err:
      # so the ncclient gives us something I don't want.  I'm going to convert
      # it and re-raise the commit error
      JXML.remove_namespaces( err.xml )
      raise CommitError( rsp=err.xml )

    return True

  ### -------------------------------------------------------------------------
  ### commit check
  ### -------------------------------------------------------------------------

  def commit_check(self):
    """
    perform a commit check.  if the commit check passes, this function
    will return :True:

    If there is a commit check error, then the RPC error reply XML
    structure will be returned
    """
    try:
      self._junos.rpc.commit_configuration( check=True )
    except Exception as err:
      return JXML.rpc_error( err.rsp )

    return True

  ### -------------------------------------------------------------------------
  ### show | compare rollback <number|0*>
  ### -------------------------------------------------------------------------

  def diff( self, **kvargs ):
    """
    retrieve a diff-format report of the candidate config against
    either the current active config, or a different rollback.

    kvargs
      'rollback' is a number [0..50]
    """

    rb_id = kvargs.get('rollback', 0)
    if rb_id < 0 or rb_id > 50:
      raise ValueError("Invalid rollback #"+str(rb_id))

    rsp = self._junos.rpc.get_configuration(dict(
      compare='rollback', rollback=str(rb_id)
      ))

    diff_txt = rsp.find('configuration-output').text
    return None if diff_txt == "\n" else diff_txt

  ### -------------------------------------------------------------------------
  ### helper on loading configs
  ### -------------------------------------------------------------------------

  def load(self, *vargs, **kvargs):
    """
    loads configuration into the device

    vargs (optional)
      is the content to load, as it would be provided to the 
      Netconf.rpc.load_config() method.  if the contents is
      a string, then you must specify kvargs['format']

    kvargs['path'] 
      path to file of configuration.  the path extension will be used
      to determine the format of the contents.
        ['conf','text','txt'] is curly-text-style
        ['set'] is set-style
        ['xml'] is XML
      the format can specific set by using kvarg['format']

    kvargs['format']
      determines the format of the contents.  options are
      ['xml','set','text'] for XML/etree, set-style, curly-brace-style

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
    rpc_xattrs = {'format':'xml'}      # junos attributes, default to XML
    rpc_contents = None

    if 'format' in kvargs:
      if kvargs['format'] == 'set': 
        rpc_xattrs['action'] = 'set'
        kvargs['format'] = 'text'
      rpc_xattrs['format'] = kvargs['format']

    if len(vargs):
      # caller is providing the content directly.
      rpc_contents = vargs[0]
      if isinstance(rpc_contents,str) and not 'format' in kvargs:
        raise RuntimeError("You must define the format of the contents")

    return self._junos.rpc.load_config( rpc_contents, **rpc_xattrs )

  ### -------------------------------------------------------------------------
  ### config exclusive
  ### -------------------------------------------------------------------------

  def lock(self):
    """
    attempts an exclusive lock on the candidate configuration
    """
    try:
      self._junos.rpc.lock_configuration()
    except Exception as err:
      # :err: is from ncclient
      raise LockError(rsp = JXML.remove_namespaces(err.xml))

    return True

  ### -------------------------------------------------------------------------
  ### releases the exclusive lock
  ### -------------------------------------------------------------------------

  def unlock( self ):
    """
    unlocks the candidate configuration
    """
    try:
      self._junos.rpc.unlock_configuration()
    except Exception as err:
      # :err: is from ncclient
      raise UnlockError(rsp = JXML.remove_namespaces(err.xml))

    return True

  ### -------------------------------------------------------------------------
  ### rollback <number|0*>
  ### -------------------------------------------------------------------------

  def rollback( self, rb_id=0 ):
    """
    rollback the candidate config to either the last active or
    a specific rollback number.
    """

    if rb_id < 0 or rb_id > 50:
      raise ValueError("Invalid rollback #"+str(rb_id))

    self._junos.rpc.load_configuration(dict(
      compare='rollback', rollback=str(rb_id)
    ))

    return True