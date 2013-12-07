# stdlib
from copy import deepcopy

# module libs
from .view import RunstatView
from .rsmfields import RunstatMakerViewFields
from .table import Table
from .optable import OpTable

class RunstatMaker(object):
  """
  Metaclass builder for RunstatTable and RunstatView.  The RunstatMaker is a namespace
  class used to build the following items:

    GetTable
      creates a "toplevel" class object for "getting" Junos run-state information,
      e.g. get-interface-information, get-route-information, etc.

    Table
      creates a table definition, used when the run-state information has one or
      more tables within the response.

    View 
      create a table view definition. a view creates the mapping of user-defined
      field names (i.e. what *they* want) to the underlying Junos XML.  the view
      is the abstraction layer between Python and Junos/XML essentially.  the
      view is defined by a dictionary of fields.

    Fields 
      creates the field definitions that construct a view.
  """

  @classmethod
  def GetTable(cls, cmd, args=None, args_key=None, item=None, key=OpTable.ITEM_NAME_XPATH, view=None, table_name=None ):
    if table_name is None: table_name = "OpTable." + cmd
    new_cls = type(table_name, (OpTable,), {} )
    new_cls.GET_RPC = cmd
    new_cls.GET_ARGS = args or {}
    if args_key is not None: new_cls.GET_KEY = args_key
    new_cls.ITEM_XPATH = item
    new_cls.ITEM_NAME_XPATH = key 
    new_cls.VIEW = view
    new_cls.__module__ = __name__
    return new_cls

  @classmethod
  def Table(cls, item, key=Table.ITEM_NAME_XPATH, view=None, table_name=None):
    if table_name is None: table_name = 'Table.' + item
    new_cls = type(table_name, (Table,), {} )
    new_cls.ITEM_XPATH = item
    new_cls.ITEM_NAME_XPATH = key 
    new_cls.VIEW = view
    new_cls.__module__ = __name__
    return new_cls

  @classmethod
  def View(cls, fields, **kvargs):
    """
    :fields: 
      dictionary of fields, structure of which is ~internal~ and should
      not be defined explicitly. use the RunstatMaker.Fields() mechanism to 
      create theserather than hardcoding the dictionary structures; 
      since they might change over time.

    :kvargs:
      'view_name' to name the class.  this could be useful for debug
      or eventual callback mechanisms.

      'groups' is a dict of name/xpath assocaited to fields
      this technique would be used to extract fields from 
      node-set elements like port <if-device-flags>.

      'extends' names the base View class to extend.  using this
      technique you can add to existing defined Views.
    """

    view_name = kvargs.get('view_name','RunstatView')
    new_cls = type(view_name, (RunstatView,), {})

    if 'extends' in kvargs:
      base_cls = kvargs['extends']
      new_cls.FIELDS = deepcopy(base_cls.FIELDS)
      new_cls.FIELDS.update(fields)
      if 'groups' in kvargs:
        new_cls.GROUPS = deepcopy(base_cls.GROUPS)
        new_cls.GROUPS.update(kvargs['groups'])
    else:
      new_cls.FIELDS = fields
      new_cls.GROUPS = kvargs['groups'] if 'groups' in kvargs else None    

    new_cls.__module__ = __name__
    return new_cls

  @classmethod
  def Fields(cls):
    """ class method that wraps the object instance """
    return RunstatMakerViewFields()




