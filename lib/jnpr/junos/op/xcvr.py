"""
Pythonifier for Xcvr Table/View
"""
from ..factory import loadyaml
from os.path import splitext
_YAML_ = splitext(__file__)[0] + '.yml'
globals().update(loadyaml(_YAML_))