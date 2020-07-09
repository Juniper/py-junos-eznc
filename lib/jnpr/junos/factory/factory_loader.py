"""
This file contains the FactoryLoader class that is used to dynamically
create Runstat Table and View objects from a <dict> of data.  The <dict> can
originate from any kind of source: YAML, JSON, program.  For examples of YAML
refer to the .yml files in this jnpr.junos.op directory.
"""
# stdlib
from copy import deepcopy
import re

from jinja2 import Environment

# locally
from jnpr.junos.factory.factory_cls import *
from jnpr.junos.factory.viewfields import *

__all__ = ["FactoryLoader"]

# internally used shortcuts

_VIEW = FactoryView
_CMDVIEW = FactoryCMDView
_FIELDS = ViewFields
_GET = FactoryOpTable
_TABLE = FactoryTable
_CFGTBL = FactoryCfgTable
_CMDTBL = FactoryCMDTable
_CMDCHILDTBL = FactoryCMDChildTable


class FactoryLoader(object):

    """
    Used to load a <dict> of data that contains Table and View definitions.

    The primary method is :load(): which will return a <dict> of item-name and
    item-class definitions.

    If you want to import these definitions directly into your namespace,
    (like a module) you would do the following:

      loader = FactoryLoader()
      catalog = loader.load( <catalog_dict> )
      globals().update( catalog )

    If you did not want to do this, you can access the items as the catalog.
    For example, if your <catalog_dict> contained a Table called MyTable, then
    you could do something like:

      MyTable = catalog['MyTable']
      table = MyTable(dev)
      table.get()
      ...
    """

    def __init__(self):
        self._catalog_dict = None  # YAML data

        self._item_optables = []  # list of the get/op-tables
        self._item_cfgtables = []  # list of get/cfg-tables
        self._item_cmdtables = []  # list of commands with unstructured data o/p
        self._item_views = []  # list of views to build
        self._item_tables = []  # list of tables to build

        self.catalog = {}  # catalog of built classes

    # -----------------------------------------------------------------------
    # Create a View class from YAML definition
    # -----------------------------------------------------------------------

    def _fieldfunc_True(self, value_rhs):
        def true_test(x):
            if value_rhs.startswith("regex("):
                return True if bool(re.search(value_rhs.strip("regex()"), x)) else False
            return x == value_rhs

        return true_test

    def _fieldfunc_False(self, value_rhs):
        def false_test(x):
            if value_rhs.startswith("regex("):
                return False if bool(re.search(value_rhs.strip("regex()"), x)) else True
            return x != value_rhs

        return false_test

    def _fieldfunc_Search(self, regex_pattern):
        def search_field(field_text):
            """ Returns the first occurrence of regex_pattern within given field_text."""
            match = re.search(regex_pattern, field_text)
            if match:
                return match.groups()[0]
            else:
                return None

        return search_field

    def _add_dictfield(self, fields, f_name, f_dict, kvargs):
        """ add a field based on its associated dictionary """
        # at present if a field is a <dict> then there is **one
        # item** - { the xpath value : the option control }.  typically
        # the option would be a bultin class type like 'int'
        # however, as this framework expands in capability, this
        # will be enhaced, yo!

        xpath, opt = list(f_dict.items())[0]  # get first/only key,value

        if opt == "group":
            fields.group(f_name, xpath)
            return

        if "flag" == opt:
            opt = "bool"  # flag is alias for bool

        # first check to see if the option is a built-in Python
        # type, most commonly would be 'int' for numbers, like counters
        if isinstance(opt, dict):
            kvargs.update(opt)
            fields.str(f_name, xpath, **kvargs)
            return

        astype = __builtins__.get(opt) or globals().get(opt)
        if astype is not None:
            kvargs["astype"] = astype
            fields.astype(f_name, xpath, **kvargs)
            return

        # next check to see if this is a "field-function"
        # operator in the form "func=value", like "True=enabled"

        if isinstance(opt, str) and opt.find("=") > 0:
            field_cmd, value_rhs = opt.split("=")
            fn_field = "_fieldfunc_" + field_cmd
            if not hasattr(self, fn_field):
                raise ValueError("Unknown field-func: '%'" % field_cmd)
            kvargs["astype"] = getattr(self, fn_field)(value_rhs)
            fields.astype(f_name, xpath, **kvargs)
            return

        raise RuntimeError("Dont know what to do with field: '%s'" % f_name)

    # ---[ END: _add_dictfield ] ---------------------------------------------

    def _add_view_fields(self, view_dict, fields_name, fields):
        """ add a group of fields to the view """
        fields_dict = view_dict[fields_name]
        try:
            # see if this is a 'fields_<group>' collection, and if so
            # then we automatically setup using the group mechanism
            mark = fields_name.index("_")
            group = {"group": fields_name[mark + 1 :]}
        except:
            # otherwise, no group, just standard 'fields'
            group = {}

        for f_name, f_data in fields_dict.items():
            # each field could have its own unique set of properties
            # so create a kvargs <dict> each time.  but copy in the
            # groups <dict> (single item) generically.
            kvargs = {}
            kvargs.update(group)

            if isinstance(f_data, dict):
                self._add_dictfield(fields, f_name, f_data, kvargs)
                continue

            if f_data in self._catalog_dict:
                # f_data is the table name
                cls_tbl = self.catalog.get(f_data, self._build_table(f_data))
                fields.table(f_name, cls_tbl)
                continue

            # if we are here, then it means that the field is a string value
            xpath = f_name if f_data is True else f_data
            fields.str(f_name, xpath, **kvargs)

    def _add_cmd_view_fields(self, view_dict, fields_name, fields):
        """ add a group of fields to the view """
        fields_dict = view_dict[fields_name]
        for f_name, f_data in fields_dict.items():
            if f_data in self._catalog_dict:
                cls_tbl = self.catalog.get(f_data, self._build_cmdtable(f_data))
                fields.table(f_name, cls_tbl)
                continue

            # if we are here, it means we need to filter fields from textfsm
            fields._fields.update({f_name: f_data})

    # -------------------------------------------------------------------------

    def _build_view(self, view_name):
        """ build a new View definition """
        if view_name in self.catalog:
            return self.catalog[view_name]

        view_dict = self._catalog_dict[view_name]
        kvargs = {"view_name": view_name}

        # if there are field groups, then get that now.
        if "groups" in view_dict:
            kvargs["groups"] = view_dict["groups"]

        # if there are eval, then get that now.
        if "eval" in view_dict:
            kvargs["eval"] = {}
            for key, exp in view_dict["eval"].items():
                env = Environment()
                kvargs["eval"][key] = env.parse(exp)

        # if this view extends another ...
        if "extends" in view_dict:
            base_cls = self.catalog.get(view_dict["extends"])
            # @@@ should check for base_cls is None!
            kvargs["extends"] = base_cls

        fields = _FIELDS()
        fg_list = [name for name in view_dict if name.startswith("fields")]
        for fg_name in fg_list:
            self._add_view_fields(view_dict, fg_name, fields)

        cls = _VIEW(fields.end, **kvargs)
        self.catalog[view_name] = cls
        return cls

    # -------------------------------------------------------------------------

    def _build_cmdview(self, view_name):
        """ build a new View definition """
        if view_name in self.catalog:
            return self.catalog[view_name]

        view_dict = self._catalog_dict[view_name]
        kvargs = {"view_name": view_name}

        if "columns" in view_dict:
            kvargs["columns"] = view_dict["columns"]
        elif "title" in view_dict:
            kvargs["title"] = view_dict["title"]
        if "regex" in view_dict:
            kvargs["regex"] = view_dict["regex"]
        if "exists" in view_dict:
            kvargs["exists"] = view_dict["exists"]
        if "filters" in view_dict:
            kvargs["filters"] = view_dict["filters"]
        if "eval" in view_dict:
            kvargs["eval"] = {}
            for key, exp in view_dict["eval"].items():
                env = Environment()
                kvargs["eval"][key] = env.parse(exp)
        fields = _FIELDS()
        fg_list = [name for name in view_dict if name.startswith("fields")]
        for fg_name in fg_list:
            self._add_cmd_view_fields(view_dict, fg_name, fields)

        cls = _CMDVIEW(fields.end, **kvargs)
        self.catalog[view_name] = cls
        return cls

    # -----------------------------------------------------------------------
    # Create a Get-Table from YAML definition
    # -----------------------------------------------------------------------

    def _build_optable(self, table_name):
        """ build a new Get-Table definition """
        if table_name in self.catalog:
            return self.catalog[table_name]

        tbl_dict = self._catalog_dict[table_name]
        kvargs = deepcopy(tbl_dict)

        rpc = kvargs.pop("rpc")
        kvargs["table_name"] = table_name

        if "view" in tbl_dict:
            view_name = tbl_dict["view"]
            cls_view = self.catalog.get(view_name, self._build_view(view_name))
            kvargs["view"] = cls_view

        cls = _GET(rpc, **kvargs)
        self.catalog[table_name] = cls
        return cls

    # -----------------------------------------------------------------------
    # Create a Get-Table from YAML definition
    # -----------------------------------------------------------------------

    def _build_cmdtable(self, table_name):
        """ build a new command-Table definition """
        if table_name in self.catalog:
            return self.catalog[table_name]

        tbl_dict = self._catalog_dict[table_name]
        kvargs = deepcopy(tbl_dict)

        if "command" in kvargs:
            cmd = kvargs.pop("command")
            kvargs["table_name"] = table_name

            if "view" in tbl_dict:
                view_name = tbl_dict["view"]
                cls_view = self.catalog.get(view_name, self._build_cmdview(view_name))
                kvargs["view"] = cls_view

            cls = _CMDTBL(cmd, **kvargs)
            self.catalog[table_name] = cls
            return cls
        elif "title" in kvargs:
            cmd = kvargs.pop("title")
            kvargs["table_name"] = table_name

            if "view" in tbl_dict:
                view_name = tbl_dict["view"]
                cls_view = self.catalog.get(view_name, self._build_cmdview(view_name))
                kvargs["view"] = cls_view

            cls = _CMDCHILDTBL(cmd, **kvargs)
            self.catalog[table_name] = cls
            return cls
        else:
            kvargs["table_name"] = table_name

            if "view" in tbl_dict:
                view_name = tbl_dict["view"]
                cls_view = self.catalog.get(view_name, self._build_cmdview(view_name))
                kvargs["view"] = cls_view

            cls = _CMDCHILDTBL(**kvargs)
            self.catalog[table_name] = cls
            return cls

    # -----------------------------------------------------------------------
    # Create a Table class from YAML definition
    # -----------------------------------------------------------------------

    def _build_table(self, table_name):
        """ build a new Table definition """
        if table_name in self.catalog:
            return self.catalog[table_name]

        tbl_dict = self._catalog_dict[table_name]

        table_item = tbl_dict.pop("item")
        kvargs = deepcopy(tbl_dict)
        kvargs["table_name"] = table_name

        if "view" in tbl_dict:
            view_name = tbl_dict["view"]
            cls_view = self.catalog.get(view_name, self._build_view(view_name))
            kvargs["view"] = cls_view

        cls = _TABLE(table_item, **kvargs)
        self.catalog[table_name] = cls
        return cls

    def _build_cfgtable(self, table_name):
        """ build a new Config-Table definition """
        if table_name in self.catalog:
            return self.catalog[table_name]
        tbl_dict = deepcopy(self._catalog_dict[table_name])

        if "view" in tbl_dict:
            # transpose name to class
            view_name = tbl_dict["view"]
            tbl_dict["view"] = self.catalog.get(view_name, self._build_view(view_name))

        cls = _CFGTBL(table_name, tbl_dict)
        self.catalog[table_name] = cls
        return cls

    # -----------------------------------------------------------------------
    # Primary builders ...
    # -----------------------------------------------------------------------

    def _sortitems(self):
        for k, v in self._catalog_dict.items():
            if "rpc" in v:
                self._item_optables.append(k)
            elif "get" in v:
                self._item_cfgtables.append(k)
            elif "set" in v:
                self._item_cfgtables.append(k)
            elif "command" in v or "title" in v:
                self._item_cmdtables.append(k)
            elif "view" in v and "item" in v and v["item"] == "*":
                self._item_cmdtables.append(k)
            elif "view" in v:
                self._item_tables.append(k)
            else:
                self._item_views.append(k)

    def load(self, catalog_dict, envrion={}):

        # load the yaml data and extract the item names.  these names will
        # become the new class definitions

        self._catalog_dict = catalog_dict
        self._sortitems()

        list(map(self._build_optable, self._item_optables))
        list(map(self._build_cfgtable, self._item_cfgtables))
        list(map(self._build_cmdtable, self._item_cmdtables))
        list(map(self._build_table, self._item_tables))
        list(map(self._build_view, self._item_views))

        return self.catalog
