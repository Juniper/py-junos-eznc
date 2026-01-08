"""
Pythonifier for BGP Table/View
"""

from os.path import splitext

from jnpr.junos.factory import loadyaml

_YAML_ = splitext(__file__)[0] + ".yml"
globals().update(loadyaml(_YAML_))
