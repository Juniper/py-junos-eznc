# stdlib
import yaml
import os.path

from .loader import ConfigLoader
from ..op import loader as RSL

__all__ = ['loadyaml']

def loadyaml( path ):
  """ YAML loader for cfgro module """
  if not any([path.endswith(x) for x in ['.yml','.yaml']]):
    path = path + '.yml'

  data_dict = yaml.load(open(path,'r').read())

  cfgro_list = [item for item in data_dict if 'get' in data_dict[item]]
  cfgro_dict = {}
  for this in cfgro_list: cfgro_dict[this] = data_dict.pop(this)

  runstat = RSL.RunstatLoader().load( data_dict )
  cfgro = ConfigLoader().load( cfgro_dict, runstat )
  cfgro.update(runstat)
  return cfgro