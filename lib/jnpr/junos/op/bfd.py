"""
Pythonifier for BFD Table/View
"""
import jnpr.junos.factory
import os
_PATH_ = os.path.splitext(__file__)[0]
globals().update(jnpr.junos.factory.load(_PATH_)
