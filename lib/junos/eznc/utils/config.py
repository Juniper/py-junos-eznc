# utils/config.py

import pdb

# package modules
from junos.eznc import RpcError
from junos.eznc import jxml as JXML

### ---------------------------------------------------------------------------
### commit
### ---------------------------------------------------------------------------

def _cfg_u_commit( junos, *vargs, **kvargs ):
  """
    commit a configuration.  returns either :True: or
    raises an RPCError exception

    :kvargs: options
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

  junos.rpc.commit_configuration( **rpc_args )
  return True

### ---------------------------------------------------------------------------
### commit check
### ---------------------------------------------------------------------------

def _cfg_u_commit_check( junos, *vargs, **kvargs):
  """
    perform a commit check.  if the commit check passes, this function
    will return :True:

    If there is a commit check error, then the RPC error reply XML
    structure will be returned
  """
  try:
    junos.rpc.commit_configuration( check=True )
  except Exception as err:
    return JXML.rpc_error( err.xml )

  return True

### ---------------------------------------------------------------------------
### show | compare rollback <number|0*>
### ---------------------------------------------------------------------------

def _cfg_u_diff( junos, *vargs, **kvargs ):
  """
    retrieve a diff-format report of the candidate config against
    either the current active config, or a different rollback.

    kvargs optional:
      rollback=<rollback-number>
  """
  rb_id = kvargs.get('rollback', 0)
  if rb_id < 0 or rb_id > 50:
    raise ValueError("Invalid rollback #"+str(rb_id))

  rsp = junos.rpc.get_configuration(dict(
    compare='rollback', rollback=str(rb_id)
    ))

  diff_txt = rsp.find('configuration-output').text
  return None if diff_txt == "\n" else diff_txt

### ---------------------------------------------------------------------------
### helper on loading configs
### ---------------------------------------------------------------------------

def _cfg_u_load( junos, *vargs, **kvargs ):
  """
    loads configuration into the device
  """
  pass

### ---------------------------------------------------------------------------
### config exclusive
### ---------------------------------------------------------------------------

def _cfg_u_lock( junos, *vargs, **kvargs ):
  """
    attempts an exclusive lock on the candidate configuration
  """
  junos.rpc.lock_configuration()
  return True

### ---------------------------------------------------------------------------
### releases the exclusive lock
### ---------------------------------------------------------------------------

def _cfg_u_unlock( junos, *vargs, **kvargs ):
  """
    unlocks the candidate configuration
  """
  junos.rpc.unlock_configuration()
  return True

### ---------------------------------------------------------------------------
### rollback <number|0*>
### ---------------------------------------------------------------------------

def _cfg_u_rollback( junos, *vargs, **kvargs ):
  """
    rollback the candidate config to either the last active or
    a specific rollback number.

    kvargs optional:
      rollback=<rollback-number>
  """

  rb_id = kvargs.get('rollback', 0)
  if rb_id < 0 or rb_id > 50:
    raise ValueError("Invalid rollback #"+str(rb_id))

  junos.rpc.load_configuration(dict(
    compare='rollback', rollback=str(rb_id)
    ))

  return True

### ---------------------------------------------------------------------------
### The following dictionary is 'exported' so that programmers can include
### it into their :Netconf: objects via the :ez: attribute
### ---------------------------------------------------------------------------

ConfigUtils = dict(
  commit = _cfg_u_commit,
  commit_check = _cfg_u_commit_check,
  diff = _cfg_u_diff,
  load = _cfg_u_load,
  lock = _cfg_u_lock,
  unlock = _cfg_u_unlock,
  rollback = _cfg_u_rollback
)
