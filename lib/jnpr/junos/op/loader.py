"""
This file contains the RunstatLoader class that is used to dynamically
create Runstat Table and View objects from a <dict> of data.  The <dict> can
originate from any kind of source: YAML, JSON, program.  For examples of YAML
refer to the .yml files in this jnpr.junos.op directory.

Refer to jnpr.junos.op.yaml for additional details.
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

  The primary method is :load(): which will return back a <dict> of 
  item-name anditem-class definition.  

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
    self.catalog_dict = None       # YAML data

    self.item_gettables = []    # list of the get-tables
    self.item_views = []        # list of views to build
    self.item_tables = []       # list of tables to build

    self.catalog = {}           # catalog of built classes

  ##### -----------------------------------------------------------------------
  ##### Create a View class from YAML definition
  ##### -----------------------------------------------------------------------

  def add_view_fields(self, view_dict, fields_name, fields):
    fields_dict = view_dict[fields_name]
    try:
      mark = fields_name.index('_')
      group = {'group':fields_name[mark+1:]}
    except:
      group={}

    for f_name, f_data in fields_dict.items():  
      kvargs = {}
      kvargs.update(group)

      if isinstance(f_data,dict):
        # for now, the only thing we are handling is the 
        # astype mechanism. nab the type looking at __builtins__
        # this is kinda a @@@ hack @@@, so we should revisit this.
        # if the user input is bad, then AttributeError exception.
        this = f_data.items()[0]
        kvargs['astype'] = __builtins__.get(this[1], str)
        fields.astype( f_name, this[0], **kvargs)
        continue

      if f_data in self.catalog_dict:
        # f_data is the table name
        cls_tbl = self.catalog.get(f_data, self.build_table( f_data ))
        fields.table( f_name, cls_tbl )
        continue        

      xpath = f_name if f_data is True else f_data
      fields.str(f_name,xpath,**kvargs)

  ### -------------------------------------------------------------------------

  def build_view(self, view_name):
    if view_name in self.catalog: return self.catalog[view_name]

    view_dict = self.catalog_dict[view_name]
    kvargs = { 'view_name' : view_name }

    # if there are field groups, then get that now.
    if 'groups' in view_dict: 
      kvargs['groups'] = view_dict['groups']

    fields = _FIELDS()
    fg_list = [name for name in view_dict if name.startswith('fields')]
    for fg_name in fg_list: 
      self.add_view_fields( view_dict, fg_name, fields )

    cls = _VIEW( fields.end, **kvargs )
    self.catalog[view_name] = cls
    return cls

  ##### -----------------------------------------------------------------------
  ##### Create a Get-Table from YAML definition
  ##### -----------------------------------------------------------------------

  def build_gettable( self, table_name):
    if table_name in self.catalog: return self.catalog[table_name]

    tbl_dict = self.catalog_dict[table_name]
    kvargs = deepcopy(tbl_dict)

    rpc = kvargs.pop('rpc')
    kvargs['table_name'] = table_name

    if 'view' in tbl_dict:
      view_name = tbl_dict['view']
      cls_view = self.catalog.get( view_name, self.build_view( view_name ))
      kvargs['view'] = cls_view

    cls = _GET(rpc, **kvargs)
    self.catalog[table_name] = cls
    return cls

  ##### -----------------------------------------------------------------------
  ##### Create a Table class from YAML definition
  ##### -----------------------------------------------------------------------

  def build_table(self, table_name ):
    if table_name in self.catalog: return self.catalog[table_name]

    tbl_dict = self.catalog_dict[table_name]

    table_item = tbl_dict.pop('item')
    kvargs = deepcopy(tbl_dict)
    kvargs['table_name'] = table_name

    if 'view' in tbl_dict:
      view_name = tbl_dict['view']
      cls_view = self.catalog.get( view_name, self.build_view( view_name ))
      kvargs['view'] = cls_view

    cls = _TABLE(table_item, **kvargs)
    self.catalog[table_name] = cls
    return cls

  ##### -----------------------------------------------------------------------
  ##### Primary builders ...
  ##### -----------------------------------------------------------------------

  def sortitems(self):
    for k,v in self.catalog_dict.items():
      if 'rpc' in v:
        self.item_gettables.append(k)
      elif 'view' in v:
        self.item_tables.append(k)
      else:
        self.item_views.append(k)

  def load( self, file_dict ):

    # load the yaml data and extract the item names.  these names will
    # become the new class definitions

    self.catalog_dict = file_dict
    self.sortitems()

    map( self.build_gettable, self.item_gettables )
    map( self.build_table, self.item_tables )
    map( self.build_view, self.item_views )

    return self.catalog