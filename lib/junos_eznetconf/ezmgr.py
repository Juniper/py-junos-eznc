class EzMgr(object):
  
  def __init__(self, junos):
    self._junos = junos

  def __call__(self, **kvargs):
    return True