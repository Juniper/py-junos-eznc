# stdlib
from inspect import isclass

class Table(object):
  ITEM_XPATH = None
  ITEM_NAME_XPATH = 'name'
  VIEW = None

  def __init__(self, dev, xml=None):
    self._dev = dev 
    self.xml = xml
    self.view = self.VIEW

  ##### -------------------------------------------------------------------------
  ##### PROPERTIES
  ##### -------------------------------------------------------------------------    

  @property 
  def D(self):
    return self._dev

  @property 
  def RPC(self):
    return self.D.rpc

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
  def hostname(self):
    return self.D.hostname

  @property 
  def is_container(self):
    """ 
    True if this table does not have records, but is a container of fields
    False otherwise
    """
    return self.ITEM_XPATH is None    

  ##### -------------------------------------------------------------------------
  ##### PRIVATE METHODS
  ##### -------------------------------------------------------------------------  

  def _assert_data(self):
    if self.xml is None: raise RuntimeError("Table is empty, use get()")    

  def _keys_composite(self, xpath, key_list):
    """ composite keys return a tuple of key-items """
#    _tkey = lambda this: tuple([this.findtext(k) for k in key_list ])
    _tkey = lambda this: tuple([this.xpath(k)[0].text for k in key_list ])
    return [_tkey(item) for item in self.xml.xpath(xpath)]

  def _keys_simple(self, xpath):
    return [x.text.strip() for x in self.xml.xpath(xpath)]

  def _keyspec(self):
    """ returns tuple (keyname-xpath, item-xpath) """    
    return (self.ITEM_NAME_XPATH, self.ITEM_XPATH)

  ##### -------------------------------------------------------------------------
  ##### PUBLIC METHODS
  ##### -------------------------------------------------------------------------    

  def items(self):
    """ returns list of tuple(name,values) for each table entry """
    return zip(self.keys(), self.values())

  def keys(self):
    """ return a list of data item keys from the Table XML """

    self._assert_data()
    key_value, xpath = self._keyspec()

    if isinstance(key_value, str):
      return self._keys_simple( xpath+'/'+key_value)

    if not isinstance( key_value, list ): 
      raise RuntimeError("What to do with key, table:'%'" % self.__class__.__name__)

    # ok, so it's a list, which means we need to extract tuple values
    return self._keys_composite( xpath, key_value )

  def values(self):
    """ returns list of table entry items() """

    self._assert_data()
    if self.view is None:
      # no View, so provide XML for each item
      return [this for this in self]
    else:
      # view object for each item
      return [this.items() for this in self]

  def get(self, *vargs, **kvargs):
    pass

  ##### -------------------------------------------------------------------------
  ##### OVERLOADS
  ##### -------------------------------------------------------------------------    

  __call__ = get

  def __repr__(self):
    cls_name = self.__class__.__name__
    if self.xml is None:
      return "%s:%s - Table empty" % (cls_name, self.D.hostname)
    else:
      n_items = len(self.keys())
      return "%s:%s: %s items" % (cls_name, self.D.hostname,n_items)

  def __len__(self):
    self._assert_data()    
    return len(self.keys())

  def __iter__(self):
    """ iterate over each time in the table """
    self._assert_data()

    as_xml = lambda table,view_xml: view_xml
    view_as = self.view or as_xml

    for this in self.xml.xpath(self.ITEM_XPATH):
      yield view_as( self, this )    

  def __getitem__(self, value):
    """
    returns a table item.  if a table view is set (should be by default) then
    the item will be converted to the view upon return.  if there is no table 
    view, then the XML object will be returned.

    :value:
      when it is a string, this will perform a select based on the key-name
      when it is a tuple, this will perform a select based on the compsite key-name
      when it is an int, this will perform a select based by position.
        nubers can be either positive or negative.
        [0] is the first item (first xpath is actually 1)
        [-1] is the last item
    """
    self._assert_data()

    namekey_xpath, item_xpath = self._keyspec()

    def get_xpath(find_value):
      if isinstance(find_value,int):
        # find by index, assuming caller is using 0-index, and might use
        # negative values to reference from end of list.  need to 
        # turn this into an XPath position value (1's based)
        xpath_pos = find_value + 1
        if find_value < 0: xpath_pos = len(self) + xpath_pos
        xpath = '%s[%s]' % (item_xpath, xpath_pos)    
        return xpath

      # otherwise we are using key=value name lookup
      # create an XPath normalized key=value filter expression
      xnkv = '[normalize-space({})="{}"]'

      if isinstance(find_value,str):
        # find by name, simple key
        return item_xpath + xnkv.format( namekey_xpath, find_value)

      if isinstance(find_value,tuple):
        # composite key (value1, value2, ...) will create an
        # iterative xpath of the fmt statement for each key/value pair
        xpf = ''.join([xnkv.format(k.replace('_','-'),v) for k,v in zip(namekey_xpath, find_value)])
        return item_xpath + xpf    

    # ---[END: get_xpath ] --------------------------------------------------------

    xpath = get_xpath( value )
    found = self.xml.xpath( xpath )
    if not len(found): return None

    as_xml = lambda table,view_xml: view_xml
    use_view = self.view or as_xml

    return use_view( table=self, view_xml=found[0] ) 