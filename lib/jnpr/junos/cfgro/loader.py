from lxml.builder import E
import yaml

def load( path ):
  if not any([path.endswith(x) for x in ['.yml','.yaml']]):
    path = path + '.yml'
  return yaml.load(open(path,'r').read())