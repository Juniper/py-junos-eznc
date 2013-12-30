"""
This file contains variables defining the filesystem paths to various
directories within the Junos PyEZ microframework
"""
from os.path import dirname as _dirname
from os.path import join as _join

MODULEDIR = _dirname(__file__)
CFGDIR = _join(MODULEPATH,'cfg')
OPDIR = _join(MODULEPATH,'op')
CFGRODIR = _join(MODULEPATH,'cfgro')
