# stdlib
from copy import deepcopy

# local
from jnpr.junos.factory.cfgtable import CfgTable
from jnpr.junos.factory.optable import OpTable
from jnpr.junos.factory.table import Table

from jnpr.junos.factory.view import View
from jnpr.junos.factory.viewfields import ViewFields

from jnpr.junos.utils.config import Config

def FactoryCfgTable(table_name=None, data_dict={}):
    if table_name is None:
        table_name = "CfgTable"
    if 'set' in data_dict.keys():
        new_cls = type(table_name, (CfgTable, Config), {})
    else:
        new_cls = type(table_name, (CfgTable,), {})
    new_cls.DEFINE = deepcopy(data_dict)
    new_cls.__module__ = __name__.replace('factory_cls', 'CfgTable')
    return new_cls


def FactoryOpTable(cmd, args=None, args_key=None, item=None,
                   key=OpTable.ITEM_NAME_XPATH, view=None, table_name=None):
    if table_name is None:
        table_name = "OpTable." + cmd
    new_cls = type(table_name, (OpTable,), {})
    new_cls.GET_RPC = cmd
    new_cls.GET_ARGS = args or {}
    if args_key is not None:
        new_cls.GET_KEY = args_key
    new_cls.ITEM_XPATH = item
    new_cls.ITEM_NAME_XPATH = key
    new_cls.VIEW = view
    new_cls.__module__ = __name__.replace('factory_cls', 'OpTable')
    return new_cls


def FactoryTable(item, key=Table.ITEM_NAME_XPATH, view=None, table_name=None):
    if table_name is None:
        table_name = 'Table.' + item
    new_cls = type(table_name, (Table,), {})
    new_cls.ITEM_XPATH = item
    new_cls.ITEM_NAME_XPATH = key
    new_cls.VIEW = view
    new_cls.__module__ = __name__.replace('factory_cls', 'Table')
    return new_cls


def FactoryView(fields, **kvargs):
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

    view_name = kvargs.get('view_name', 'RunstatView')
    new_cls = type(view_name, (View,), {})

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

    new_cls.__module__ = __name__.replace('factory_cls', 'View')
    return new_cls
