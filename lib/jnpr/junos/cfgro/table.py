from lxml.builder import E

class Table(object):

  def __init__(self, dev, data_dict):
    self._dev = dev
    self._data_dict = data_dict
    xpkeys = self.getkeys
    self._xpathkeys = xpkeys if len(xpkeys) else None

  @property 
  def D(self):
    return self._dev

  @property 
  def getkeys(self):
    return [k[4:] for k in self._data_dict.keys() if k.startswith('key_')]

  def _buildxml( self, namesonly=True ):
    """
    Return an lxml Element starting with <configuration> and comprised
    of the elements specified in the xpath expression.

    For example, and xpath = 'interfaces/interface' would product:

     <configuration>
        <interfaces>
          <interface/>
        </interfaces>
      </configuration>

    If :namesonly: is True, then the XML will be encoded only to
    retrieve the XML name keys at the 'end' of the XPath expression.

    This return value can then be passed to dev.rpc.get_config() 
    to retrieve the specifc data
    """
    xpath = self._data_dict['get']    
    top = E('configuration')
    dot = top
    for name in xpath.split('/'):
      dot.append(E(name))
      dot = dot[0]

    if namesonly is True: dot.attrib['recurse'] = 'false'
    return top

  def _get_encode_keys(self, get_cmd, kvargs):
    def _grindkey( key_name, key_value ):
      """ create the XML child elements (list) for the XML parent key """

      key_xpath = self._data_dict['key_'+key_name]
      if isinstance(key_xpath,str):
        # simple key/value, but return as list
        return [E(key_xpath, key_value)]

      # key is a list (composite-key)
      return [E(xp,xv) for xp,xv in zip(key_xpath, key_value)]

    for key_name in self._xpathkeys:
      # create an XML element with the key/value 
      key_value = kvargs.get(key_name)
      if key_value is None: 
        raise RuntimeError("Missing key value for: '%s'" % key_name)
      add_keylist_xml = _grindkey(key_name, key_value)

      # now link this item into the XML command
      dot = get_cmd.find('.//' + key_name)
      if dot is None:
        raise RuntimeError("Unable to find parent XML for key: '%'" % key_name )
      for _at,_add in enumerate(add_keylist_xml): dot.insert(_at,_add)


  def get(self, **kvargs):
    """
    Retrieve configuration data for this table. :kvargs: are used to 
    provide any xpath key=value information.
    """
    get_cmd = self._buildxml()    

    if self._xpathkeys is not None: 
      self._get_encode_keys( get_cmd, kvargs )
    
    self.xml = self.D.rpc.get_config( get_cmd )
    return True    

  def _keys_composite(self, xpath, key_list):
    """ composite keys return a tuple of key-items """
    _tkey = lambda this: tuple([this.findtext(k) for k in key_list ])
    return [_tkey(item) for item in self.xml.xpath(xpath)]

  def keys(self ):
    key_value = self._data_dict.get('key','name')
    xpath = self._data_dict['get']

    if isinstance(key_value, str):
      xpath +=  "/" + key_value
      return [x.text.strip() for x in self.xml.xpath(xpath)]

    if not isinstance( key_value, list ): 
      raise RuntimeError("What to do with key, table:'%'" % self.__class__.__name__)

    # ok, so it's a list, which means we need to extract tuple values
    return self._keys_composite( xpath, key_value )