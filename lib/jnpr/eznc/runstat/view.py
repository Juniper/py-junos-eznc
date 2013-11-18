from lxml import etree

class RunstatView(object):
  NAME_XPATH = 'name'
  FIELD_AS_INT = []
  FIELD_AS = {}

  def __init__(self,as_xml):
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

  @property 
  def fields(self):
    return self.FIELD_XPATH.keys()

  def keys(self):
    return self.fields 

  def values(self):
    return [getattr(self,field) for field in self.fields]

  def items(self):
    return zip(self.keys(), self.values())

  @property 
  def name(self):
    return self._xml.findtext(self.NAME_XPATH).strip()

  def __repr__(self):
    return "%s(%s)" % (self.__class__.__name__, self.name)

  def __getattr__(self,name):
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
