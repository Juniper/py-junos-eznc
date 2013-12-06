
# stdlib
from copy import deepcopy

# local
from .table import Table 

def ConfigLoaderMakeTableClass(table_name=None, data_dict={} ):
  if table_name is None: table_name = "CfgGetTable"
  new_cls = type(table_name, (Table,), {} )
  new_cls.DEFINE = deepcopy(data_dict)
  new_cls.__module__ = __name__
  return new_cls

_MKTBL = ConfigLoaderMakeTableClass

class ConfigLoader(object):
  def __init__(self):
    self.catalog = {}

  def _build_gettable( self, table_name):
    """ build a new Get-Table definition """
    if table_name in self.catalog: return self.catalog[table_name]

    tbl_dict = self._catalog_dict[table_name]

    if 'view' in tbl_dict:
      # transpose name to class
      tbl_dict['view'] = self._environ.get( tbl_dict['view'] )

    cls = _MKTBL( table_name, tbl_dict )
    self.catalog[table_name] = cls
    return cls

  def load( self, catalog_dict, environ={} ):
    self._catalog_dict = catalog_dict
    self._environ = environ
    for table in catalog_dict: self._build_gettable(table)
    return self.catalog
