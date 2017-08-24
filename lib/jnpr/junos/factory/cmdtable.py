import re

# 3rd-party
from lxml import etree

# local
from jnpr.junos.factory.table import Table
from jnpr.junos.jxml import remove_namespaces

# stdlib
from inspect import isclass
from time import time
from datetime import datetime
import os

# 3rd-party
from lxml import etree

import json
from jnpr.junos.factory.to_json import TableJSONEncoder

_TSFMT = "%Y%m%d%H%M%S"


class CMDTable(object):
    # ITEM_FILTER = 'name'

    def __init__(self, dev=None, output=None, path=None):
        """
        :dev: Device instance
        :xml: lxml Element instance
        :path: file path to XML, to be used rather than :dev:
        """
        self._dev = dev
        self.xml = output
        self.view = self.VIEW
        self.ITEM_FILTER = 'name'
        self._key_list = []
        self._path = path

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    def get(self, *vargs, **kvargs):
        """
        Retrieve the XML table data from the Device instance and
        returns back the Table instance - for call-chaining purposes.

        If the Table was created with a :path: rather than a Device,
        then this method will load the XML from that file.  In this
        case, the \*vargs, and \**kvargs are not used.

        ALIAS: __call__

        :vargs:
          [0] is the table :arg_key: value.  This is used so that
          the caller can retrieve just one item from the table without
          having to know the Junos RPC argument.

        :kvargs:
          these are the name/value pairs relating to the specific Junos
          XML command attached to the table.  For example, if the RPC
          is 'get-route-information', there are parameters such as
          'table' and 'destination'.  Any valid RPC argument can be
          passed to :kvargs: to further filter the results of the :get():
          operation.  neato!

        NOTES:
          If you need to create a 'stub' for unit-testing
          purposes, you want to create a subclass of your table and
          overload this methods.
        """
        self._clearkeys()

        if self._path is not None:
            # for loading from local file-path
            with open(self._path, 'r') as fp:
                self.data = fp.read().strip()
            if self.data.startswith('<output>'):
                self.data = re.search(r'^<output>(.*)</outout>$',
                                      self.data).group(1)
            return self

        # execute the Junos RPC to retrieve the table
        if hasattr(self, 'TARGET'):
            rpc_args = {'target': self.TARGET,
                         'command': self.GET_CMD}
            self.xml = getattr(self.RPC, 'request_pfe_execute')(**rpc_args)
            self.data = self.xml.text
        else:
            self.data = self.CLI(self.GET_CMD)
        print self.data

        # returning self for call-chaining purposes, yo!
        return self

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def D(self):
        """ the Device instance """
        return self._dev

    @property
    def CLI(self):
        """ the Device.cli instance """
        return self.D.cli

    @property
    def RPC(self):
        """ the Device.rpc instance """
        return self.D.rpc

    @property
    def view(self):
        """ returns the current view assigned to this table """
        return self._view

    @view.setter
    def view(self, cls):
        """ assigns a new view to the table """
        if cls is None:
            self._view = None
            return

        if not isclass(cls):
            raise ValueError("Must be given RunstatView class")

        self._view = cls

    @property
    def hostname(self):
        return self.D.hostname

    @property
    def is_container(self):
        """
        True if this table does not have records, but is a container of fields
        False otherwise
        """
        return self.ITEM_XPATH is None

    @property
    def key_list(self):
        """ the list of keys, as property for caching """
        return self._key_list

    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------

    def _assert_data(self):
        if self.data is None:
            raise RuntimeError("Table is empty, use get()")

    def _tkey(self, this, key_list):
        """ keys with missing XPATH nodes are set to None """
        keys = []
        for k in key_list:
            try:
                keys.append(this.xpath(k)[0].text)
            except BaseException:
                keys.append(None)
        return tuple(keys)

    def _keys_composite(self, xpath, key_list):
        """ composite keys return a tuple of key-items """
        return [self._tkey(item, key_list) for item in self.xml.xpath(xpath)]

    def _keys_simple(self, xpath):
        return [x.text.strip() for x in self.xml.xpath(xpath)]

    def _keyspec(self):
        """ returns tuple (keyname-xpath, item-xpath) """
        return (self.ITEM_NAME_FILTER, self.ITEM_FILTER)

    def _clearkeys(self):
        self._key_list = []

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    # ------------------------------------------------------------------------
    # keys
    # ------------------------------------------------------------------------

    def _keys(self):
        """ return a list of data item keys from the data string """

        self._assert_data()
        key_value, xpath = self._keyspec()

        if isinstance(key_value, str):
            # Check if pipe is in the key_value, if so append xpath
            # to each value
            if ' | ' in key_value:
                return self._keys_simple(' | '.join([xpath + '/' + x for x in
                                                     key_value.split(' | ')]))
            return self._keys_simple(xpath + '/' + key_value)

        if not isinstance(key_value, list):
            raise RuntimeError(
                "What to do with key, table:'%s'" %
                self.__class__.__name__)

        # ok, so it's a list, which means we need to extract tuple values
        return self._keys_composite(xpath, key_value)

    def keys(self):
        # if the key_list has been cached, then use it
        if len(self.key_list):
            return self.key_list

        # otherwise, build the list of keys into the cache
        self._key_list = self._keys()
        return self._key_list

    # ------------------------------------------------------------------------
    # values
    # ------------------------------------------------------------------------

    def values(self):
        """ returns list of table entry items() """

        self._assert_data()
        if self.view is None:
            # no View, so provide XML for each item
            return [this for this in self]
        else:
            # view object for each item
            return [list(this.items()) for this in self]

    # ------------------------------------------------------------------------
    # items
    # ------------------------------------------------------------------------

    def items(self):
        """ returns list of tuple(name,values) for each table entry """
        return list(zip(self.keys(), self.values()))

    def to_json(self):
        """
        :returns: JSON encoded string of entire Table contents
        """
        return json.dumps(self, cls=TableJSONEncoder)

    # -------------------------------------------------------------------------
    # OVERLOADS
    # -------------------------------------------------------------------------

    __call__ = get

    def __repr__(self):
        cls_name = self.__class__.__name__
        source = self.D.hostname if self.D is not None else self._path

        if self.xml is None:
            return "%s:%s - Table empty" % (cls_name, source)
        else:
            n_items = len(self.keys())
            return "%s:%s: %s items" % (cls_name, source, n_items)

    def __len__(self):
        self._assert_data()
        return len(self.keys())

    def __iter__(self):
        """ iterate over each time in the table """
        self._assert_data()

        def as_xml(table, view_xml): return view_xml
        view_as = self.view or as_xml

        for this in self.xml.xpath(self.ITEM_XPATH):
            yield view_as(self, this)

    def __getitem__(self, value):
        """
        returns a table item. If a table view is set (should be by default)
        then the item will be converted to the view upon return.  if there is
        no table view, then the XML object will be returned.

        :value:
          for <string>, this will perform a select based on key-name
          for <tuple>, this will perform a select based on compsite key-name
          for <int>, this will perform a select based by position, like <list>
            [0] is the first item
            [-1] is the last item
          when it is a <slice> then this will return a <list> of View widgets
        """
        self._assert_data()
        keys = self.keys()

        if isinstance(value, int):
            # if selection by index, then grab the key at this index and
            # recursively call this method using that key, yo!
            return self.__getitem__(keys[value])

        if isinstance(value, slice):
            # implements the 'slice' mechanism
            return [self.__getitem__(key) for key in keys[value]]

        # ---[ get_xpath ] ----------------------------------------------------

        def get_xpath(find_value):
            namekey_xpath, item_xpath = self._keyspec()
            xnkv = '[{0}="{1}"]'

            if isinstance(find_value, str):
                # find by name, simple key
                return item_xpath + xnkv.format(namekey_xpath, find_value)

            if isinstance(find_value, tuple):
                # composite key (value1, value2, ...) will create an
                # iterative xpath of the fmt statement for each key/value pair
                # skip over missing keys
                kv = []
                for k, v in zip(namekey_xpath, find_value):
                    if v is not None:
                        kv.append(xnkv.format(k.replace('_', '-'), v))
                xpf = ''.join(kv)
                return item_xpath + xpf

        # ---[END: get_xpath ] ------------------------------------------------

        found = self.xml.xpath(get_xpath(value))
        if not len(found):
            return None

        def as_xml(table, view_xml): return view_xml
        use_view = self.view or as_xml

        return use_view(table=self, view_xml=found[0])

    def __contains__(self, key):
        """ membership for use with 'in' """
        return bool(key in self.keys())
