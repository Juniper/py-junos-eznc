from contextlib import contextmanager
from copy import deepcopy
from lxml import etree

class RunstatView(object):
  """
  RunstatView is the base-class that makes extracting values from XML 
  data appear as objects with attributes.
  """

  NAME_XPATH = 'name'
  FIELDS = {}
  GROUPS = None

  ### -------------------------------------------------------------------------
  ### CONSTRUCTOR
  ### -------------------------------------------------------------------------

  def __init__(self, table, view_xml):
    """
    :table:
      instance of the RunstatTable

    :view_xml:
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

    if self.GROUPS is not None:
      self._groups = {}
      for xg_name,xg_xpath in self.GROUPS.items():
        xg_xml = view_xml.xpath(xg_xpath)
        if not len(xg_xml):  # @@@ this is technically an error; need to trap it
          continue
        self._groups[xg_name] = xg_xml[0]

  ### -------------------------------------------------------------------------
  ### PROPERTIES
  ### -------------------------------------------------------------------------

  @property 
  def name(self):
    """ return the name of view item """
    if self.NAME_XPATH is None: return self._table.N.hostname
    return self._xml.findtext(self.NAME_XPATH).strip()

  # ALIAS key <=> name
  key = name

  @property
  def xml(self):
    """ returns the XML associated to the item """
    return self._xml
   
  ### -------------------------------------------------------------------------
  ### METHODS
  ### -------------------------------------------------------------------------

  def keys(self):
    """ list of view keys, i.e. field names """
    return self.FIELDS.keys()

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
    return "%s\n@%s" % (self.__class__.__name__, self.name)

  def __getattr__(self,name):
    """ 
    returns a view item value, called as :obj.name:
    """
    item = self.FIELDS.get(name)
    if item is None:
      raise ValueError("Unknown field: '%s'" % name)

    if item.has_key('table'):
      found = item['table'](ncdev=self._table.N, table_xml=self._xml)
    else:
      as_type = item.get('as_type',str)
      if item.has_key('group'):
        found = self._groups[item['group']].xpath(item['xpath'])
      else:
        found = self._xml.xpath(item['xpath'])

      if 0 == len(found): 
        # even for the case of numbers, do not set the value.  we 
        # want to detect "does not exist" vs. defaulting to 0
        # -- 2013-nov-19, JLS.
        return None      
      try:
        # added exception handler to catch malformed xpath expressesion
        # -- 2013-nov-19, JLS.
        as_str = found[0] if isinstance(found[0],str) else found[0].text
        found = as_type(as_str.strip())
      except:
        raise RuntimeError("Unable to handle field:'%s'" % name)

    return found

  def __getitem__(self,name):
    """ 
    allow the caller to extract field values using :obj['name']:
    the same way they would do :obj.name:
    """
    return getattr(self,name)




