"""
This file contains the RunstatLoader class that is used to dynamically
create Runstat Table and View objects from a <dict> of data.  The <dict> can
originate from any kind of source: YAML, JSON, program.  For examples of YAML
refer to the .yml files in this jnpr.junos.op directory.
"""
# stdlib
from copy import deepcopy

# locally
from . import RunstatMaker as _RSM

__all__ = ['RunstatLoader']

# internally used shortcuts

_VIEW = _RSM.View
_FIELDS = _RSM.Fields
_GET = _RSM.GetTable 
_TABLE = _RSM.Table 

class RunstatLoader(object):
  """
  Used to load a <dict> of data that contains Table and View definitions.

  The primary method is :load(): which will return a <dict> of item-name and
  item-class definitions.  

  If you want to import these definitions directly into your namespace, (like a module)
  you would do the following:

    loader = RunstatLoader()
    catalog = loader.load( <catalog_dict> )
    globals().update( catalog )

  If you did not want to do this, you can access the items as the catalog.  For 
  example, if your <catalog_dict> contained a Table called MyTable, then you could do
  something like:

    MyTable = catalog['MyTable']
    table = MyTable(dev)
    table.get()
    ...
  """  
  def __init__(self):
    self._catalog_dict = None       # YAML data

    self._item_gettables = []    # list of the get-tables
    self._item_views = []        # list of views to build
    self._item_tables = []       # list of tables to build

    self.catalog = {}           # catalog of built classes

  ##### -----------------------------------------------------------------------
  ##### Create a View class from YAML definition
  ##### -----------------------------------------------------------------------

  def _add_dictfield(self, fields, f_name, f_dict, kvargs ):
    """ add a field based on its associated dictionary """
    # at present if a field is a <dict> then there is one
    # item, the xpath value and the option control.  typically
    # the option would be a bultin class type like :int:
    # however, as this framework expands in capability, this
    # will be enhaced, yo!

    xpath, opt = f_dict.items()[0]

    # flag is alias for bool
    if 'flag' == opt: opt = 'bool'   

    astype = __builtins__.get(opt)
    if astype is not None:
      kvargs['astype'] = astype
      fields.astype( f_name, xpath, **kvargs)
      return
    else:
      raise RuntimeError("Dont know what to do with: %s" % f_name)

  def _add_view_fields(self, view_dict, fields_name, fields):
    """ add a group of fields to the view """
    fields_dict = view_dict[fields_name]
    try:
      # see if this is a 'fields_<group>' collection, and if so
      # then we automatically setup using the group mechanism
      mark = fields_name.index('_')
      group = {'group':fields_name[mark+1:]}
    except:
      # otherwise, no group, just standard 'fields'
      group={}

    for f_name, f_data in fields_dict.items():  
      # each field could have its own unique set of properties
      # so create a kvargs <dict> each time.  but copy in the
      # groups <dict> (single item) generically.
      kvargs = {}
      kvargs.update(group)

      if isinstance(f_data,dict):
        self._add_dictfield( fields, f_name, f_data, kvargs )
        continue

      if f_data in self._catalog_dict:
        # f_data is the table name
        cls_tbl = self.catalog.get(f_data, self._build_table( f_data ))
        fields.table( f_name, cls_tbl )
        continue        

      # if we are here, then it means that the field is a string value
      xpath = f_name if f_data is True else f_data
      fields.str(f_name,xpath,**kvargs)

  ### -------------------------------------------------------------------------

  def _build_view(self, view_name):
    """ build a new View definition """
    if view_name in self.catalog: return self.catalog[view_name]

    view_dict = self._catalog_dict[view_name]
    kvargs = { 'view_name' : view_name }

    # if there are field groups, then get that now.
    if 'groups' in view_dict: 
      kvargs['groups'] = view_dict['groups']

    fields = _FIELDS()
    fg_list = [name for name in view_dict if name.startswith('fields')]
    for fg_name in fg_list: 
      self._add_view_fields( view_dict, fg_name, fields )

    cls = _VIEW( fields.end, **kvargs )
    self.catalog[view_name] = cls
    return cls

  ##### -----------------------------------------------------------------------
  ##### Create a Get-Table from YAML definition
  ##### -----------------------------------------------------------------------

  def _build_gettable( self, table_name):
    """ build a new Get-Table definition """
    if table_name in self.catalog: return self.catalog[table_name]

    tbl_dict = self._catalog_dict[table_name]
    kvargs = deepcopy(tbl_dict)

    rpc = kvargs.pop('rpc')
    kvargs['table_name'] = table_name

    if 'view' in tbl_dict:
      view_name = tbl_dict['view']
      cls_view = self.catalog.get( view_name, self._build_view( view_name ))
      kvargs['view'] = cls_view

    cls = _GET(rpc, **kvargs)
    self.catalog[table_name] = cls
    return cls

  ##### -----------------------------------------------------------------------
  ##### Create a Table class from YAML definition
  ##### -----------------------------------------------------------------------

  def _build_table(self, table_name ):
    """ build a new Table definition """
    if table_name in self.catalog: return self.catalog[table_name]

    tbl_dict = self._catalog_dict[table_name]

    table_item = tbl_dict.pop('item')
    kvargs = deepcopy(tbl_dict)
    kvargs['table_name'] = table_name

    if 'view' in tbl_dict:
      view_name = tbl_dict['view']
      cls_view = self.catalog.get( view_name, self._build_view( view_name ))
      kvargs['view'] = cls_view

    cls = _TABLE(table_item, **kvargs)
    self.catalog[table_name] = cls
    return cls

  ##### -----------------------------------------------------------------------
  ##### Primary builders ...
  ##### -----------------------------------------------------------------------

  def _sortitems(self):
    for k,v in self._catalog_dict.items():
      if 'rpc' in v:
        self._item_gettables.append(k)
      elif 'view' in v:
        self._item_tables.append(k)
      else:
        self._item_views.append(k)

  def load( self, file_dict ):

    # load the yaml data and extract the item names.  these names will
    # become the new class definitions

    self._catalog_dict = file_dict
    self._sortitems()

    map( self._build_gettable, self._item_gettables )
    map( self._build_table, self._item_tables )
    map( self._build_view, self._item_views )

    return self.catalog