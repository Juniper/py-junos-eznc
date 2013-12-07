
# stdlib
from copy import deepcopy


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
