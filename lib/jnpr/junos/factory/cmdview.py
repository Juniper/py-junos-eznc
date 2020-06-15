class CMDView(object):

    """
    View is the base-class that makes extracting values from XML
    data appear as objects with attributes.
    """

    KEY = "name"
    KEY_ITEMS = []
    COLUMNS = {}
    FILTERS = None
    FIELDS = {}
    REGEX = {}
    EXISTS = {}
    GROUPS = None
    TITLE = None
    EVAL = {}

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

    def asview(self, view_cls):
        """ create a new View object for this item """
        return view_cls(self._table, self._xml)

    # -------------------------------------------------------------------------
    # OVERLOADS
    # -------------------------------------------------------------------------

    def __repr__(self):
        """ returns the name of the View with the associate item name """
        return "%s:%s" % (self.__class__.__name__, self.name)

    def __getitem__(self, name):
        """
        allow the caller to extract field values using :obj['name']:
        the same way they would do :obj.name:
        """
        return getattr(self, name)
