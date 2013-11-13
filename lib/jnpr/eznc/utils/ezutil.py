class EzUtil(object):
  """ Base class for all utility classes """
  
  def __init__(self,dev):
    self._dev = dev

  def __repr__(self):
    return "%s(%s)" % (self.__class__.__name__, self._dev.hostname)