# stdlib
from inspect import isclass

# 3rd-party modules
from lxml import etree

# local module
from .runstat import Runstat

class RunstatTable(Runstat):
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
    if not issubclass(cls,Runstat):
      raise ValueError("Must be given RunstatView class, given: '%s'" % cls.__name__)

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
    """ select a specific table item by :name: and return the view or XML """
    self.assert_data()

    if self.ITER_XPATH is None:
      # this is a table of tables; i.e. not table of record views
      found = self.got
    else:
      xpath = self.ITER_XPATH + '[normalize-space(%s)="' % self.NAME_XPATH + value + '"]'
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
