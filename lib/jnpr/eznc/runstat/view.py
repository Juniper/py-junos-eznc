from contextlib import contextmanager
from copy import deepcopy
from lxml import etree

class RunstatView(object):
  """
  RunstatView is the base-class that makes extracting values from XML 
  data appear as objects with attributes.
  """

  NAME_XPATH = 'name'
  FIELD_AS_INT = []
  FIELD_AS = {}

  def __init__(self,as_xml):
    """
    :as_xml:
      this should be an lxml etree Elemenet object.  This 
      constructor also accepts a list with a single item/XML
    """
    # if as_xml is passed as a list, make sure it only has
    # a single item, common response from an xpath search
    if isinstance(as_xml,list):
      if 1 == len(as_xml):
        as_xml = as_xml[0]
      else:
        raise ValueError("constructor only accepts a single item")

    # now ensure that the thing provided is an lxml etree Element
    if not isinstance(as_xml,etree._Element):
      raise ValueError("constructor only accecpts lxml.etree._Element")  

    self._xml = as_xml

  def __repr__(self):
    """ returns the name of the View with the associate items name """
    return "%s(%s)" % (self.__class__.__name__, self.name)

  @property 
  def fields(self):
    """ list of view field names """
    return self.FIELD_XPATH.keys()

  def keys(self):
    """ list of view keys, i.e. field names """
    return self.fields 

  def values(self):
    """ list of view values """
    return [getattr(self,field) for field in self.fields]

  def items(self):
    """ list of tuple(key,value) """
    return zip(self.keys(), self.values())

  @property 
  def name(self):
    """ return the name of view item """
    return self._xml.findtext(self.NAME_XPATH).strip()

  def __getattr__(self,name):
    """ retrieve a view field item value """
    xpath = self.FIELD_XPATH.get(name)
    if xpath is None:
      raise ValueError("Unkown field: '%s'" % name)

    found = self._xml.xpath(xpath)
    len_found = len(found)
    if 0 == len_found: return None

    # @@@ need to handle multi-found case
    found = found[0].text.strip()
    if name in self.FIELD_AS_INT:
      found = int(found)
    elif name in self.FIELD_AS:
      found = self.FIELD_AS[name](found)

    return found

  @contextmanager
  def extend(self):
    """ 
    provide the ability for subclassing objects to extend the
    definitions of the fields.  this is implemented as a 
    context manager with the form called from the subclass 
    constructor:

      with self.extend() as more:
        more.field_xpath = <dict>
        more.fied_as_int = <list>   # optinal
        more.field_as = <dict>      # optional

    """
    self.FIELD_XPATH = deepcopy(self.__class__.FIELD_XPATH)

    class MoreView(object): pass
    more = MoreView()
    yield more

    self.FIELD_XPATH.update(more.field_xpath)

    if hasattr(more,'field_as_int'):
      self.FIELD_AS_INT = deepcopy(self.__class__.FIELD_AS_INT)
      self.FIELD_AS_INT += more.field_as_int

    if hasattr(more,'field_as'):
      self.FIELD_AS = deepcopy(self.__class__.FIELD_AS)
      self.FIELD_AS.update(more.field_as)




