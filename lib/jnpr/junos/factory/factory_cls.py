# stdlib
from copy import deepcopy

# local
from jnpr.junos.factory.cfgtable import CfgTable
from jnpr.junos.factory.optable import OpTable
from jnpr.junos.factory.cmdtable import CMDTable
from jnpr.junos.factory.table import Table

from jnpr.junos.factory.view import View
from jnpr.junos.factory.cmdview import CMDView

from jnpr.junos.utils.config import Config


def FactoryCfgTable(table_name=None, data_dict={}):
    if table_name is None:
        table_name = "CfgTable"
    if "set" in data_dict.keys():
        new_cls = type(table_name, (CfgTable, Config), {})
    else:
        new_cls = type(table_name, (CfgTable,), {})
    new_cls.DEFINE = deepcopy(data_dict)
    new_cls.__module__ = __name__.replace("factory_cls", "CfgTable")
    return new_cls


def FactoryOpTable(
    cmd,
    args=None,
    args_key=None,
    item=None,
    key=OpTable.ITEM_NAME_XPATH,
    view=None,
    table_name=None,
    use_filter=True,
):
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
    new_cls.USE_FILTER = use_filter
    new_cls.__module__ = __name__.replace("factory_cls", "OpTable")
    return new_cls


def FactoryCMDTable(
    cmd,
    args=None,
    item=None,
    key_items=None,
    key="name",
    view=None,
    table_name=None,
    title=None,
    delimiter=None,
    eval=None,
    platform="juniper_junos",
    use_textfsm=False,
    **kwargs
):
    new_cls = type(table_name, (CMDTable,), {})
    new_cls.GET_CMD = cmd
    if "target" in kwargs:
        new_cls.TARGET = kwargs["target"]
    new_cls.KEY_ITEMS = key_items
    new_cls.CMD_ARGS = args or {}
    new_cls.ITEM = item
    new_cls.KEY = key
    new_cls.VIEW = view
    new_cls.TITLE = title
    new_cls.DELIMITER = delimiter
    new_cls.EVAL = eval
    new_cls.PLATFORM = platform
    new_cls.USE_TEXTFSM = use_textfsm
    new_cls.__module__ = __name__.replace("factory_cls", "CMDTable")
    return new_cls


def FactoryCMDChildTable(
    title=None,
    regex=None,
    key="name",
    delimiter=None,
    table_name=None,
    view=None,
    key_items=None,
    item=None,
    eval=None,
):
    new_cls = type(table_name, (CMDTable,), {})
    new_cls.DELIMITER = delimiter
    new_cls.KEY = key
    new_cls.REGEX = regex
    new_cls.TITLE = title
    new_cls.VIEW = view
    new_cls.KEY_ITEMS = key_items
    new_cls.ITEM = item
    new_cls.EVAL = eval
    new_cls.__module__ = __name__.replace("factory_cls", "CMDTable")
    return new_cls


def FactoryTable(
    item, key=Table.ITEM_NAME_XPATH, view=None, table_name=None, use_filter=True
):
    if table_name is None:
        table_name = "Table." + item
    new_cls = type(table_name, (Table,), {})
    new_cls.ITEM_XPATH = item
    new_cls.ITEM_NAME_XPATH = key
    new_cls.VIEW = view
    new_cls.USE_FILTER = use_filter
    new_cls.__module__ = __name__.replace("factory_cls", "Table")
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

    view_name = kvargs.get("view_name", "RunstatView")
    new_cls = type(view_name, (View,), {})

    if "extends" in kvargs:
        base_cls = kvargs["extends"]
        new_cls.FIELDS = deepcopy(base_cls.FIELDS)
        new_cls.FIELDS.update(fields)
        if "groups" in kvargs:
            new_cls.GROUPS = deepcopy(base_cls.GROUPS)
            new_cls.GROUPS.update(kvargs["groups"])
    else:
        new_cls.FIELDS = fields
        new_cls.GROUPS = kvargs["groups"] if "groups" in kvargs else None

    if "eval" in kvargs:
        new_cls.EVAL = kvargs["eval"]
        new_cls.FIELDS.update(kvargs["eval"])

    new_cls.__module__ = __name__.replace("factory_cls", "View")
    return new_cls


def FactoryCMDView(fields, **kvargs):
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

    view_name = kvargs.get("view_name", "RunstatView")
    new_cls = type(view_name, (CMDView,), {})

    if "columns" in kvargs:
        new_cls.COLUMNS = deepcopy(kvargs["columns"])
    elif "title" in kvargs:
        new_cls.TITLE = deepcopy(kvargs["title"])
    if "regex" in kvargs:
        new_cls.REGEX = deepcopy(kvargs["regex"])
    if "exists" in kvargs:
        new_cls.EXISTS = deepcopy(kvargs["exists"])
    if "filters" in kvargs:
        new_cls.FILTERS = deepcopy(kvargs["filters"])
    if fields is not None:
        new_cls.FIELDS = fields
    if "eval" in kvargs:
        new_cls.EVAL = kvargs["eval"]
        # new_cls.FIELDS.update(kvargs['eval'])

    new_cls.__module__ = __name__.replace("factory_cls", "CMDView")
    return new_cls
