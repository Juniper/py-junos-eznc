# stdlib
from inspect import isclass

# 3rd-party modules
from lxml import etree

class RunstatTable(object):
  """
  DOCUMENT-ME
  """
  ITER_XPATH = None
  NAME_XPATH = 'name'
  VIEW = None

  ### -------------------------------------------------------------------------
  ### CONSTRUCTOR
  ### -------------------------------------------------------------------------

  def __init__(self, ncdev, table_xml = None):
    self._ncdev = ncdev
    self._xml_got = table_xml
    self.view = self.VIEW

  ### -------------------------------------------------------------------------
  ### PROPERTIES
  ### -------------------------------------------------------------------------

  @property
  def D(self):
    """ shortcut to the Device instance """
    return self._ncdev

  @property
  def R(self):
    """ shortcut to the Device RPC metaexec instance """
    return self._ncdev.rpc

  @property
  def xml(self):
    """ 
    returns the XML data received from the device.  for tables within
    tables, this XML will be the parent XML element that contains the
    table contents.
    """
    return self._xml_got

  @property
  def got(self):
    """ returns the XML data recieved from the device """
    return self.xml

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
  def is_container(self):
    """ 
    True if this table does not have records, but is a container of fields
    False otherwise
    """
    return self.ITER_XPATH is None

  @property 
  def can_refresh(self):
    """
    True if this table has an 'arg_key' that allows for simple retreval
    of items based on names
    """
    return hasattr(self,'GET_KEY')

  @property
  def _iter_xpath(self):
    """ internal use only """
    return self.got.xpath(self.ITER_XPATH) if self.got is not None else []
  
  ### -------------------------------------------------------------------------
  ### METHODS
  ### -------------------------------------------------------------------------

  def assert_data(self):
    """ ensure that the table has XML data """
    if self._xml_got is None: raise RuntimeError("No data")

  def _rpc_get(self, argkey=None, **kvargs):
    args = {}                     # create empty <dict>
    args.update(self.GET_ARGS)    # copy default args
    args.update(kvargs)           # copy caller provided args

    if hasattr(self, 'GET_KEY') and argkey is not None:
      args.update({self.GET_KEY: argkey })

    return getattr(self.R,self.GET_RPC)(**args)

  def get(self, *vargs, **kvargs):
    """ 
    Retrieve the XML table data from the Device instance and
    returns back the Table instance - for call-chaining purposes.  

    ALIAS: read, __call__    

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

    argkey = vargs[0] if len(vargs) else None

    # execute the Junos RPC to retrieve the table
    self._xml_got = self._rpc_get(argkey, **kvargs)

    # returning self for call-chaining purposes, yo!
    return self

  def keys(self):
    """ returns a list of table item names """
    if self.is_container: return []
    return [n.findtext(self.NAME_XPATH).strip() for n in self._iter_xpath]

  def values(self):
    """ 
    returns list of table entry items().  
    """
    if self.view is None:
      # no View, so provide XML for each item
      return [this for this in self]
    else:
      # view object for each item
      return [this.items() for this in self]

  def items(self):
    """ returns list of tuple(name,values) for each table entry """
    return zip(self.keys(), self.values())

  ### -------------------------------------------------------------------------
  ### ALIASES
  ### -------------------------------------------------------------------------

  read = get

  ### -------------------------------------------------------------------------
  ### OVERLOADS
  ### -------------------------------------------------------------------------

  def __repr__(self):
    cname = self.__class__.__name__
    if self.is_container is not None:
      return "%s:%s: %s items" % (cname, self.D.hostname, len(self))
    else:
      return "%s:%s: data=%s" % (cname, self.D.hostname, ('no','yes')[self.got is not None])

  # make callable alias to :get(): 
  __call__ = get

  # ---------------------------------------------------------------------------
  # len is the number of items in the table
  # ---------------------------------------------------------------------------

  def __len__(self):
    return 1 if self.is_container else len(self._iter_xpath)

  # ---------------------------------------------------------------------------
  # [<name>]: select a table item based on <name>
  # [0]: gives the only view, for composite table
  # ---------------------------------------------------------------------------

  def __getitem__(self,value):
    """
    returns a table item.  if a table view is set (should be by default) then
    the item will be converted to the view upon return.  if there is no table 
    view, then the XML object will be returned.

    :value:
      when it is a string, this will perform a select based on the name
      when it is a number, this will perform a select based by position.
        nubers can be either positive or negative.
        [0] is the first item (first xpath is actually 1)
        [-1] is the last item
    """
    self.assert_data()

    use_view = self.view

    def get_xpath(find_value):
      if isinstance(find_value,str):
        # find by name
        xpath = self.ITER_XPATH + '[normalize-space(%s)="' % self.NAME_XPATH + find_value + '"]'
      elif isinstance(find_value,int):
        # find by index, assuming caller is using 0-index, and might use
        # negative values to reference from end of list
        xpath_pos = find_value + 1
        if find_value < 0:
          xpath_pos = len(self) + xpath_pos
        xpath = '%s[%s]' % (self.ITER_XPATH, xpath_pos)
      return xpath

    if self.ITER_XPATH is None:
      # this is a table of tables; i.e. not table of record views
      found = self.got
    else:
      if isinstance(value,tuple):
        # tuple(name,view_cls)
        use_view = value[1]        
        value = value[0]

      xpath = get_xpath(value)
      found = self.got.xpath(xpath)
      if not len(found): return None
      found = found[0]

    return use_view(table=self, view_xml=found) if use_view is not None else found

  # ---------------------------------------------------------------------------
  # iterate though each item in the talbe, not applicable for composite table
  # ---------------------------------------------------------------------------

  def __iter__(self):
    """ iteratable of each toplevel xpath item """
    self.assert_data()
    itself = lambda x: x
    view = lambda x: self.view(self, x)

    item_as = view if self.view else itself

    for this in self.got.xpath(self.ITER_XPATH):
      yield item_as(this)
