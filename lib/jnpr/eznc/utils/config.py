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

  def load(self):
    """
    loads configuration into the device
    """
    raise RuntimeError("need to implement!")

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