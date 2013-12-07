# stdlib
from copy import deepcopy 

# local
from .cfgtable import CfgTable 

def FactoryCfgTable(table_name=None, data_dict={} ):
  if table_name is None: table_name = "CfgTable"
  new_cls = type(table_name, (CfgTable,), {} )
  new_cls.DEFINE = deepcopy(data_dict)
  new_cls.__module__ = __name__
  return new_cls

