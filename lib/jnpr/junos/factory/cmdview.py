import warnings
from contextlib import contextmanager
from copy import deepcopy
import json
import sys

from jnpr.junos.factory.viewfields import ViewFields
from jnpr.junos.factory.to_json import TableViewJSONEncoder


class CMDView(object):

    """
    View is the base-class that makes extracting values from XML
    data appear as objects with attributes.
    """

    KEY = 'name'
    KEY_ITEMS = []
    COLUMN = {}
    FIELDS = {}
    GROUPS = None
    TITLE = None

    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------

    def __init__(self, table, data):
        """
        :table:
          instance of the RunstatTable

        :data:
          this should data
        """
        pass

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def T(self):
        """ return the Table instance for the View """
        return self._table

    @property
    def D(self):
        """ return the Device instance for this View """
        return self.T.D

    @property
    def name(self):
        """ return the name of view item """
        if self.ITEM_NAME_XPATH is None:
            return self._table.D.hostname
        if isinstance(self.ITEM_NAME_XPATH, str):
            # xpath union key
            if ' | ' in self.ITEM_NAME_XPATH:
                return self._xml.xpath(self.ITEM_NAME_XPATH)[0].text.strip()
            # simple key
            return self._xml.findtext(self.ITEM_NAME_XPATH).strip()
        else:
            # composite key
            # keys with missing XPATH nodes are set to None
            keys = []
            for i in self.ITEM_NAME_XPATH:
                try:
                    keys.append(self.xml.xpath(i)[0].text.strip())
                except:
                    keys.append(None)
            return tuple(keys)

    # ALIAS key <=> name
    key = name

    @property
    def xml(self):
        """ returns the XML associated to the item """
        return self._xml

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------

    def keys(self):
        """ list of view keys, i.e. field names """
        return self.FIELDS.keys()

    def values(self):
        """ list of view values """
        return [getattr(self, field) for field in self.keys()]

    def items(self):
        """ list of tuple(key,value) """
        return zip(self.keys(), self.values())

    def _updater_instance(self, more):
        """ called from extend """
        if hasattr(more, 'column'):
            self.COLUMN = deepcopy(self.__class__.COLUMN)
            self.COLUMN.update(more.column.end)

        if hasattr(more, 'title'):
            self.TITLE = deepcopy(self.__class__.TITLE)
            self.TITLE.update(more.title.end)

        if hasattr(more, 'fields'):
            self.FIELDS = deepcopy(self.__class__.FIELDS)
            self.FIELDS.update(more.fields.end)

        if hasattr(more, 'groups'):
            self.GROUPS = deepcopy(self.__class__.GROUPS)
            self.GROUPS.update(more.groups)

    def _updater_class(self, more):
        """ called from extend """
        if hasattr(more, 'column'):
            self.COLUMN.update(more.column.end)

        if hasattr(more, 'title'):
            self.TITLE.update(more.title.end)

        if hasattr(more, 'fields'):
            self.FIELDS.update(more.fields.end)

        if hasattr(more, 'groups'):
            self.GROUPS.update(more.groups)

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

        more = type('RunstatViewMore', (object,), {})()
        if fields is True:
            more.fields = ViewFields()

        # ---------------------------------------------------------------------
        # callback through context manager
        # ---------------------------------------------------------------------

        yield more
        updater = self._updater_class if all is True else \
            self._updater_instance
        updater(more)

    def asview(self, view_cls):
        """ create a new View object for this item """
        return view_cls(self._table, self._xml)

    def to_json(self):
        """
        :returns: JSON encoded string of entire View contents
        """
        return json.dumps(self, cls=TableViewJSONEncoder)

    # -------------------------------------------------------------------------
    # OVERLOADS
    # -------------------------------------------------------------------------

    def __repr__(self):
        """ returns the name of the View with the associate item name """
        return "%s:%s" % (self.__class__.__name__, self.name)

    def __getattr__(self, name):
        """
        returns a view item value, called as :obj.name:
        """
        item = self.FIELDS.get(name)
        if item is None:
            raise ValueError("Unknown field: '%s'" % name)

        if 'table' in item:
            # if this is a sub-table, then return that now
            return item['table'](self.D, self._xml)

        # otherwise, not a sub-table, and handle the field
        astype = item.get('astype', str)
        if 'group' in item:
            if item['group'] in self._groups:
                found = self._groups[item['group']].xpath(item['xpath'])
            else:
                return
        else:
            found = self._xml.xpath(item['xpath'])

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
                if sys.version < '3':
                    as_str = x if isinstance(x, str) else x.text
                    if isinstance(as_str, unicode):
                        as_str = as_str.encode('ascii', 'replace')
                else:
                    as_str = x if isinstance(x, str) else x.text
                if as_str is not None:
                    as_str = as_str.strip()
                if not as_str:
                    as_str = x.tag     # use 'not' to test for empty
                return astype(as_str)

            if 1 == len_found:
                return _munch(found[0])
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
