from ..factory import loadyaml
_yml_file = __file__.split('.')[0]+'.yml'
globals().update(loadyaml(_yml_file))