"""
This file contains variables defining the filesystem paths to various
directories within the Junos PyEZ microframework
"""
from os.path import dirname as _dirname
from os.path import join as _join

MODULEPATH = _dirname(__file__)
CFG = _join(MODULEPATH,'cfg')
OP = _join(MODULEPATH,'op')
CFGRO = _join(MODULEPATH,'cfgro')
