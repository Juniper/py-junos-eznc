from .. import Resource
from .classic import PhyPortClassic 
from .switch import PhyPortSwitch

__all__ = ['PhyPort']

class PhyPort(object):
  def __new__(cls, dev, name=None):
    supercls = { 
      'CLASSIC' : PhyPortClassic,
      'SWITCH'  : PhyPortSwitch, 
    }.get( dev.facts['ifd_style'] )
    newcls = type(cls.__name__, (supercls,), {})
    return newcls(dev, name)


