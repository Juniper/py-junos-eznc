# stdlib
from inspect import isclass
from time import time
from datetime import datetime
import os

# 3rd-party
from lxml import etree

_TSFMT = "%Y%m%d%H%M%S"

import json
from jnpr.junos.factory.to_json import TableJSONEncoder


class Table(object):
    ITEM_XPATH = None
    ITEM_NAME_XPATH = 'name'
    VIEW = None

    def __init__(self, dev=None, xml=None, path=None):
        """
        :dev: Device instance
        :xml: lxml Element instance
        :path: file path to XML, to be used rather than :dev:
        """
        self._dev = dev
        self.xml = xml
        self.view = self.VIEW
        self._key_list = []
        self._path = path
        self._lxml = xml

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def D(self):
        """ the Device instance """
        return self._dev

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
        if self.xml is None:
            raise RuntimeError("Table is empty, use get()")

    def _tkey(self, this, key_list):
        """ keys with missing XPATH nodes are set to None """
        keys = []
        for k in key_list:
            try:
                keys.append(this.xpath(k)[0].text)
            except:
                keys.append(None)
        return tuple(keys)

    def _keys_composite(self, xpath, key_list):
        """ composite keys return a tuple of key-items """
        return [self._tkey(item, key_list) for item in self.xml.xpath(xpath)]

    def _keys_simple(self, xpath):
        return [x.text.strip() for x in self.xml.xpath(xpath)]

    def _keyspec(self):
        """ returns tuple (keyname-xpath, item-xpath) """
        return (self.ITEM_NAME_XPATH, self.ITEM_XPATH)

    def _clearkeys(self):
        self._key_list = []

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    # ------------------------------------------------------------------------
    # keys
    # ------------------------------------------------------------------------

    def _keys(self):
        """ return a list of data item keys from the Table XML """

        self._assert_data()
        key_value, xpath = self._keyspec()

        if isinstance(key_value, str):
            # Check if pipe is in the key_value, if so append xpath to each value
            if ' | ' in key_value:
                return self._keys_simple(' | '.join([xpath + '/' + x for x in key_value.split(' | ')]))
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

    # ------------------------------------------------------------------------
    # get - loads the data from source
    # ------------------------------------------------------------------------

    def get(self, *vargs, **kvargs):
        # implemented by either OpTable or CfgTable
        # @@@ perhaps this should raise an exception rather than just 'pass',??
        pass

    # ------------------------------------------------------------------------
    # savexml - saves the table XML to a local file
    # ------------------------------------------------------------------------

    def savexml(self, path, hostname=False, timestamp=False, append=None):
        """
        Save a copy of the table XML data to a local file.  The name of the
        output file (:path:) can include the name of the Device host, the
        timestamp of this action, as well as any user-defined appended value.
        These 'add-ons' will be added to the :path: value prior to the file
        extension in the order (hostname,timestamp,append), separated by
        underscore (_).

        For example, if both hostname=True and append='BAZ1', then when
        :path: = '/var/tmp/foo.xml' and the Device.hostname is "srx123", the
        final file-path will be "/var/tmp/foo_srx123_BAZ1.xml"

        :path:
          file-path to write the XML file on the local filesystem

        :hostname:
          if True, will append the hostname to the :path:

        :timestamp:
          if True, will append the timestamp to the :path: using the default
            timestamp format
          if <str> the timestamp will use the value as the timestamp format as
            defied by strftime()

        :append:
          any <str> value that you'd like appended to the :path: value
          preceding the filename extension.
        """
        fname, fext = os.path.splitext(path)

        if hostname is True:
            fname += "_%s" % self.D.hostname

        if timestamp is not False:
            tsfmt = _TSFMT if timestamp is True else timestamp
            tsfmt_val = datetime.fromtimestamp(time()).strftime(tsfmt)
            fname += "_%s" % tsfmt_val

        if append is not None:
            fname += "_%s" % append

        path = fname + fext
        return etree.ElementTree(self.xml).write(open(path, 'w'))

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

        as_xml = lambda table, view_xml: view_xml
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

        as_xml = lambda table, view_xml: view_xml
        use_view = self.view or as_xml

        return use_view(table=self, view_xml=found[0])

    def __contains__(self, key):
        """ membership for use with 'in' """
        return bool(key in self.keys())
