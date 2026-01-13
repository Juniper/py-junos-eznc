from typing import Any, ClassVar, Dict, List, Optional


class CMDView(object):
    """
    View is the base-class that makes extracting values from XML
    data appear as objects with attributes.
    """

    KEY: ClassVar[str] = "name"
    KEY_ITEMS: ClassVar[List[str]] = []
    COLUMNS: ClassVar[Dict[str, Any]] = {}
    FILTERS: ClassVar[Optional[Any]] = None
    FIELDS: ClassVar[Dict[str, Any]] = {}
    REGEX: ClassVar[Dict[str, Any]] = {}
    EXISTS: ClassVar[Dict[str, Any]] = {}
    GROUPS: ClassVar[Optional[Any]] = None
    TITLE: ClassVar[Optional[str]] = None
    EVAL: ClassVar[Dict[str, Any]] = {}

    _table: Any
    _xml: Any
    name: Optional[str]

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

    def asview(self, view_cls):
        """create a new View object for this item"""
        return view_cls(self._table, self._xml)

    # -------------------------------------------------------------------------
    # OVERLOADS
    # -------------------------------------------------------------------------

    def __repr__(self):
        """returns the name of the View with the associate item name"""
        return "%s:%s" % (self.__class__.__name__, self.name)

    def __getitem__(self, name):
        """
        allow the caller to extract field values using :obj['name']:
        the same way they would do :obj.name:
        """
        return getattr(self, name)
