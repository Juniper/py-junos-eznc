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
  def N(self):
    return self._ncdev

  @property
  def R(self):
    return self._ncdev.rpc

  @property
  def got(self):
    return self._xml_got

  @property
  def view(self):
    return self._view

  @view.setter
  def view(self, cls):
    """ :cls: must either be a RunstatView or None """

    if cls is None:
      self._view = None
      return

    if not isclass(cls):
      raise ValueError("Must be given RunstatView class")

    self._view = cls

  @property
  def _iter_xpath(self):
    return self.got.xpath(self.ITER_XPATH) if self.got is not None else []
  
  ### -------------------------------------------------------------------------
  ### METHODS
  ### -------------------------------------------------------------------------

  def assert_data(self):
    if self._xml_got is None: raise RuntimeError("No data")

  def get(self, **kvargs):
    args = {}
    args.update(self.GET_ARGS)
    args.update(kvargs)
    self._xml_got = getattr(self.R,self.GET_RPC)(**args)

  def keys(self):
    if self.ITER_XPATH is None: return []
    return [n.findtext(self.NAME_XPATH).strip() for n in self._iter_xpath]

  ### -------------------------------------------------------------------------
  ### OVERLOADS
  ### -------------------------------------------------------------------------

  def __repr__(self):
    cname = self.__class__.__name__
    if self.ITER_XPATH is not None:
      return "%s(%s): %s items" % (cname, self.N.hostname, len(self))
    else:
      return "%s(%s): data=%s" % (cname, self.N.hostname, ('no','yes')[self.got is not None])

  def __len__(self):
    return len(self._iter_xpath)

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

    if self.ITER_XPATH is None:
      # this is a table of tables; i.e. not table of record views
      found = self.got
    else:
      if isinstance(value,str):
        # find by name
        xpath = self.ITER_XPATH + '[normalize-space(%s)="' % self.NAME_XPATH + value + '"]'
      elif isinstance(value,int):
        # find by index, assuming caller is using 0-index, and might use
        # negative values to reference from end of list
        xpath_pos = value + 1
        if value < 0:
          xpath_pos = len(self) + xpath_pos
        xpath = '%s[%s]' % (self.ITER_XPATH, xpath_pos)

      found = self.got.xpath(xpath)
      if not len(found): return None
      found = found[0]

    return self.view(table=self, view_xml=found) if self.view is not None else found

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
