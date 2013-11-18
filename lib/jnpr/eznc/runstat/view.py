from pdb import set_trace

from contextlib import contextmanager
from copy import deepcopy
from lxml import etree

from .runstat import Runstat

class RunstatView(Runstat):
  """
  RunstatView is the base-class that makes extracting values from XML 
  data appear as objects with attributes.
  """

  NAME_XPATH = 'name'
  FIELD_XPATH = {}
  FIELD_AS = {}

  ### -------------------------------------------------------------------------
  ### CONSTRUCTOR
  ### -------------------------------------------------------------------------

  def __init__(self, table, view_xml):
    """
    :table:
      instance of the RunstatTable

    :as_xml:
      this should be an lxml etree Elemenet object.  This 
      constructor also accepts a list with a single item/XML
    """
    # if as_xml is passed as a list, make sure it only has
    # a single item, common response from an xpath search
    if isinstance(view_xml,list):
      if 1 == len(view_xml):
        view_xml = view_xml[0]
      else:
        raise ValueError("constructor only accepts a single item")

    # now ensure that the thing provided is an lxml etree Element
    if not isinstance(view_xml,etree._Element):
      raise ValueError("constructor only accecpts lxml.etree._Element")  

    self._table = table
    self._xml = view_xml
    self.NAME_XPATH = table.NAME_XPATH

  ### -------------------------------------------------------------------------
  ### PROPERTIES
  ### -------------------------------------------------------------------------

  @property 
  def name(self):
    """ return the name of view item """
    if self.NAME_XPATH is None: return self._table.N.hostname
    return self._xml.findtext(self.NAME_XPATH).strip()

  ### -------------------------------------------------------------------------
  ### METHODS
  ### -------------------------------------------------------------------------

  def keys(self):
    """ list of view keys, i.e. field names """
    return self.FIELD_XPATH.keys()

  def values(self):
    """ list of view values """
    return [getattr(self,field) for field in self.keys()]

  def items(self):
    """ list of tuple(key,value) """
    return zip(self.keys(), self.values())

  @contextmanager
  def extend(self):
    """ 
    provide the ability for subclassing objects to extend the
    definitions of the fields.  this is implemented as a 
    context manager with the form called from the subclass 
    constructor:

      with self.extend() as more:
        more.field_xpath = <dict>
        more.field_as = <dict>      # optional

    """
    self.FIELD_XPATH = deepcopy(self.__class__.FIELD_XPATH)

    class MoreView(object): pass
    more = MoreView()
    yield more

    self.FIELD_XPATH.update(more.field_xpath)

    if hasattr(more,'field_as'):
      self.FIELD_AS = deepcopy(self.__class__.FIELD_AS)
      self.FIELD_AS.update(more.field_as)

  ### -------------------------------------------------------------------------
  ### OVERLOADS
  ### -------------------------------------------------------------------------

  def __repr__(self):
    """ returns the name of the View with the associate item name """
    return "%s(%s)" % (self.__class__.__name__, self.name)

  def __getattr__(self,name):
    """ returns a view value by item :name: """
    xpath = self.FIELD_XPATH.get(name)
    if xpath is None:
      raise ValueError("Unknown field: '%s'" % name)

    field_as = self.FIELD_AS.get(name,str)
    if issubclass(field_as, Runstat):
      _xpath_dot = self._xml.getroottree().getpath(self._xml)
      # then this is RunstatTable class.  once we have this,
      found = field_as(ncdev=self._table.N, table_xml=self._xml)
      found._xpath_dot = _xpath_dot
    else:
      found = self._xml.xpath(xpath)
      if 0 == len(found): return None      
      found = field_as(found[0].text.strip())

    return found

  def __getitem__(self,name):
    """ same as getattr """
    return getattr(self,name)



