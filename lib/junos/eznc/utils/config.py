# utils/config.py


def _cfg_u_commit( junos, *vargs, **kvargs ):
  """
    commit a configuration
  """
  pass

def _cfg_u_commit_check( junos, *vargs, **kvargs):
  """
    perform a commit check
  """
  pass

def _cfg_u_diff( junos, *vargs, **kvargs ):
  """
    retrieve a diff-format report of the candidate config against
    either the current active config, or a different rollback.

    kvargs optional:
      rollback=<rollback-number>
  """
  pass

def _cfg_u_load( junos, *vargs, **kvargs ):
  """
    loads configuration into the device
  """
  pass

def _cfg_u_lock( junos, *vargs, **kvargs ):
  """
    attempts an exclusive lock on the candidate configuration
  """
  pass

def _cfg_u_unlock( junos, *vargs, **kvargs ):
  """
    unlocks the candidate configuration
  """
  pass

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


ConfigUtils = dict(
  commit = _cfg_u_commit,
  commit_check = _cfg_u_commit_check,
  diff = _cfg_u_diff,
  load = _cfg_u_load,
  lock = _cfg_u_lock,
  unlock = _cfg_u_unlock,
  rollback = _cfg_u_rollback
)
