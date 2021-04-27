import warnings
from contextlib import contextmanager
from copy import deepcopy
from lxml import etree
import json
import sys
from jinja2 import Template, meta

from jnpr.junos.factory.viewfields import ViewFields
from jnpr.junos.factory.to_json import TableViewJSONEncoder


class View(object):

    """
    View is the base-class that makes extracting values from XML
    data appear as objects with attributes.
    """

    ITEM_NAME_XPATH = "name"
    FIELDS = {}
    EVAL = {}
    GROUPS = None

    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------

    def __init__(self, table, view_xml):
        """
        :table:
          instance of the RunstatTable

        :view_xml:
          this should be an lxml etree Elemenet object.  This
          constructor also accepts a list with a single item/XML
        """
        # if as_xml is passed as a list, make sure it only has
        # a single item, common response from an xpath search
        if isinstance(view_xml, list):
            if 1 == len(view_xml):
                view_xml = view_xml[0]
            else:
                raise ValueError("constructor only accepts a single item")

        # now ensure that the thing provided is an lxml etree Element
        if not isinstance(view_xml, etree._Element):
            raise ValueError("constructor only accecpts lxml.etree._Element")

        self._table = table
        self.ITEM_NAME_XPATH = table.ITEM_NAME_XPATH
        self._init_xml(view_xml)

    def _init_xml(self, given_xml):
        self._xml = given_xml
        if self.GROUPS is not None:
            self._groups = {}
            for xg_name, xg_xpath in self.GROUPS.items():
                xg_xml = self._xml.xpath(xg_xpath)
                # @@@ this is technically an error; need to trap it
                if not len(xg_xml):
                    continue
                self._groups[xg_name] = xg_xml[0]

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def T(self):
        """return the Table instance for the View"""
        return self._table

    @property
    def D(self):
        """return the Device instance for this View"""
        return self.T.D

    @property
    def name(self):
        """return the name of view item"""
        if self.ITEM_NAME_XPATH is None:
            return []
            # return self._table.D.hostname
        if isinstance(self.ITEM_NAME_XPATH, str):
            # xpath union key
            if " | " in self.ITEM_NAME_XPATH:
                if "Null" in self.ITEM_NAME_XPATH:
                    return self._check_key_delimiter_null(
                        self._xml, self.ITEM_NAME_XPATH
                    )
                return self._xml.xpath(self.ITEM_NAME_XPATH)[0].text.strip()
            # simple key
            return self._xml.findtext(self.ITEM_NAME_XPATH).strip()
        else:
            # composite key
            # keys with missing XPATH nodes are set to None
            keys = []
            for item_name_xpath in self.ITEM_NAME_XPATH:
                if " | " in item_name_xpath:
                    key_with_null_cleaned = self._check_key_delimiter_null(
                        self._xml, item_name_xpath
                    )
                    if key_with_null_cleaned:
                        keys.append(key_with_null_cleaned)
                else:
                    try:
                        keys.append(self.xml.xpath(item_name_xpath)[0].text.strip())
                    except:
                        keys.append(None)
            if keys:
                return tuple(keys)
            else:
                return keys

    # ALIAS key <=> name
    key = name

    def _check_key_delimiter_null(self, xml, item_name_xpath):
        """
        Case where key is provided like key: re-name | Null

        :param xml: xml object retrieved from device
        :param item_name_xpath: key xpath
        :return: key if fetched else []
        """
        if "Null" in item_name_xpath:
            # Let try get value for valid xpath key
            xpath_key = [x for x in item_name_xpath.split(" | ") if x != "Null"]
            if xpath_key:
                val = xml.xpath(xpath_key[0])
                if val:
                    return val[0].text.strip()
                else:
                    # To handle Null key
                    return []

    @property
    def xml(self):
        """returns the XML associated to the item"""
        return self._xml

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    def keys(self):
        """list of view keys, i.e. field names"""
        return self.FIELDS.keys()

    def values(self):
        """list of view values"""
        return [getattr(self, field) for field in self.keys()]

    def items(self):
        """list of tuple(key,value)"""
        return zip(self.keys(), self.values())

    def _updater_instance(self, more):
        """called from extend"""
        if hasattr(more, "fields"):
            self.FIELDS = deepcopy(self.__class__.FIELDS)
            self.FIELDS.update(more.fields.end)

        if hasattr(more, "groups"):
            self.GROUPS = deepcopy(self.__class__.GROUPS)
            self.GROUPS.update(more.groups)

        if hasattr(more, "eval"):
            self.EVAL = deepcopy(self.__class__.EVAL)
            self.EVAL.update(more.eval)

    def _updater_class(self, more):
        """called from extend"""
        if hasattr(more, "fields"):
            self.FIELDS.update(more.fields.end)

        if hasattr(more, "groups"):
            self.GROUPS.update(more.groups)

        if hasattr(more, "eval"):
            self.EVAL.update(more.eval)

    @contextmanager
    def updater(self, fields=True, groups=False, all=True, **kvargs):
        """
        provide the ability for subclassing objects to extend the
        definitions of the fields.  this is implemented as a
        context manager with the form called from the subclass
        constructor:

          with self.extend() as more:
            more.fields = <dict>
            more.groups = <dict>   # optional
        """
        # ---------------------------------------------------------------------
        # create a new object class so we can attach stuff to it arbitrarily.
        # then pass that object to the caller, yo!
        # ---------------------------------------------------------------------

        more = type("RunstatViewMore", (object,), {})()
        if fields is True:
            more.fields = ViewFields()

        # ---------------------------------------------------------------------
        # callback through context manager
        # ---------------------------------------------------------------------

        yield more
        updater = self._updater_class if all is True else self._updater_instance
        updater(more)

    def asview(self, view_cls):
        """create a new View object for this item"""
        return view_cls(self._table, self._xml)

    def refresh(self):
        """
        ~~~ EXPERIMENTAL ~~~
        refresh the data from the Junos device.  this only works if the table
        provides an "args_key", does not update the original table, just this
        specific view/item
        """
        warnings.warn("Experimental method: refresh")

        if self._table.can_refresh is not True:
            raise RuntimeError("table does not support this feature")

        # create a new table instance that gets only the specific named
        # value of this view

        tbl_xml = self._table._rpc_get(self.name)
        new_xml = tbl_xml.xpath(self._table.ITEM_XPATH)[0]
        self._init_xml(new_xml)
        return self

    def to_json(self):
        """
        :returns: JSON encoded string of entire View contents
        """
        return json.dumps(self, cls=TableViewJSONEncoder)

    # -------------------------------------------------------------------------
    # OVERLOADS
    # -------------------------------------------------------------------------

    def __repr__(self):
        """returns the name of the View with the associate item name"""
        return "%s:%s" % (self.__class__.__name__, self.name)

    def __getattr__(self, name):
        """
        returns a view item value, called as :obj.name:
        """
        expression = self.EVAL.get(name)
        if expression:
            variables = meta.find_undeclared_variables(expression)
            t = Template(expression)
            expression = t.render({k: self.__getitem__(k) for k in variables})
            val = eval(expression)
            setattr(self, name, val)
            return val

        item = self.FIELDS.get(name)
        if item is None:
            raise ValueError("Unknown field: '%s'" % name)

        if "table" in item:
            # if this is a sub-table, then return that now
            return item["table"](self.D, self._xml)

        # otherwise, not a sub-table, and handle the field
        astype = item.get("astype", str)
        if "group" in item:
            if item["group"] in self._groups:
                found = self._groups[item["group"]].xpath(item["xpath"])
            else:
                return
        else:
            found = self._xml.xpath(item["xpath"])

        len_found = len(found)

        if astype is bool:
            # handle the boolean flag case separately
            return bool(len_found)

        if not len_found:
            # even for the case of numbers, do not set the value.  we
            # want to detect "does not exist" vs. defaulting to 0
            # -- 2013-nov-19, JLS.
            return None

        try:
            # added exception handler to catch malformed xpath expressesion
            # -- 2013-nov-19, JLS.
            # added support to handle multiple xpath values, i.e. a list of
            # things that have the same xpath expression (common in configs)
            # -- 2031-dec-06, JLS
            # added support to use the element tag if the text is empty
            def _munch(x):
                if sys.version < "3":
                    as_str = x if isinstance(x, str) else x.text
                    if isinstance(as_str, unicode):
                        as_str = as_str.encode("ascii", "replace")
                else:
                    as_str = x if isinstance(x, str) else x.text
                if as_str is not None:
                    as_str = as_str.strip()
                if not as_str:
                    as_str = x.tag  # use 'not' to test for empty
                return astype(as_str)

            if 1 == len_found:
                return _munch(found[0])
            # -- 2020-March-26, if  string function (like string-before or string-after) is used as xpath (instead of as xpath condition), lxml will return ElementUnicodeResult object, which will be converted wrongly by the next interation, we should return the original UnicodeResult
            if isinstance(found, etree._ElementUnicodeResult):
                return found

            return [_munch(this) for this in found]

        except:
            raise RuntimeError("Unable to handle field:'%s'" % name)

        # and if we are here, then we didn't handle the field.
        raise RuntimeError("Unable to handle field:'%s'" % name)

    def __getitem__(self, name):
        """
        allow the caller to extract field values using :obj['name']:
        the same way they would do :obj.name:
        """
        return getattr(self, name)
