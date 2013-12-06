from lxml.builder import E

class Table(object):

  ##### -----------------------------------------------------------------------
  ##### CONSTRUCTOR
  ##### -----------------------------------------------------------------------

  def __init__(self, dev, data_dict):
    self._dev = dev
    self._data_dict = data_dict
    self.xml = None

  ##### -----------------------------------------------------------------------
  ##### PROPERTIES
  ##### -----------------------------------------------------------------------

  @property 
  def D(self):
    return self._dev

  @property 
  def required_keys(self):
    """ 
    return a list of the keys required when invoking :get(): 
    and :get_keys(): 
    """
#    return [k[4:] for k in self._data_dict.keys() if k.startswith('key_')]
    return self._data_dict.get('required_keys')

  @property 
  def keys_required(self):
    """ True/False - if this Table requires keys """
    return self.required_keys is not None

  ##### -----------------------------------------------------------------------
  ##### OVERLOADS
  ##### -----------------------------------------------------------------------

  def __repr__(self):
    cls_name = self.__class__.__name__
    if self.xml is None:
      return "%s:%s - Table empty" % (cls_name, self.D.hostname)
    else:
      n_items = len(self.keys())
      return "%s:%s - %s items" % (cls_name, self.D.hostname,n_items)

  ##### -----------------------------------------------------------------------
  ##### PRIVATE METHODS
  ##### -----------------------------------------------------------------------

  def _buildxml( self, namesonly=True ):
    """
    Return an lxml Element starting with <configuration> and comprised
    of the elements specified in the xpath expression.

    For example, and xpath = 'interfaces/interface' would produce:

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

  def _grindkey(self, key_xpath, key_value ):
    """ returns list of XML elements for key values """
    simple = lambda: [E(key_xpath.replace('_','-'), key_value)]
    composite = lambda: [E(xp.replace('_','-'),xv) for xp,xv in zip(key_xpath, key_value)]
    return simple() if isinstance(key_xpath,str) else composite()

  def _encode_requiredkeys(self, get_cmd, kvargs):
    """ 
    used to encode the required_keys values into the XML get-command.
    each of the required_key=<value> pairs are defined in :kvargs:
    """
    rqkeys = self._data_dict['required_keys']
    for key_name in self.required_keys:
      # create an XML element with the key/value 
      key_value = kvargs.get(key_name)
      if key_value is None: 
        raise ValueError("Missing required-key: '%s'" % key_name)
      key_xpath = rqkeys[key_name]
      add_keylist_xml = self._grindkey(key_xpath, key_value)

      # now link this item into the XML command, where key_name
      # designates the XML parent element
      dot = get_cmd.find('.//' + key_name.replace('_','-'))
      if dot is None:
        raise RuntimeError("Unable to find parent XML for key: '%'" % key_name )
      for _at,_add in enumerate(add_keylist_xml): dot.insert(_at,_add)

  def _encode_namekey(self, get_cmd, dot, namekey_value):
    """
    encodes the specific namekey into the get command so that the 
    returned XML configuration is the complete hierarchy of data. to 
    do this, we also need to remove the 'recurse=false' attribute that
    was added in _buildxml
    """
    namekey_xpath = self._data_dict.get('key','name')
    keylist_xml = self._grindkey(namekey_xpath, namekey_value)
    for _add in keylist_xml: dot.append(_add)
    del dot.attrib['recurse']   

  def _encode_getfields( self, get_cmd, dot ):
    for field_xpath in self._data_dict['get_fields']:
      dot.append(E(field_xpath))

  ### -------------------------------------------------------------------------
  ### get - retrieve Table data
  ### -------------------------------------------------------------------------

  def get(self, **kvargs):
    """
    Retrieve configuration data for this table. :kvargs: are used to 
    provide any required_key=value information.

    RESERVED :kvargs:
      'key' - used to retrieve the contents of the table record, and not 
      just the list of keys (default)
    """
    if self.keys_required is True and not len(kvargs):
      raise ValueError("This table has required-keys", self.required_keys)

    get_cmd = self._buildxml()    

    if self.keys_required is True: 
      self._encode_requiredkeys( get_cmd, kvargs )

    if 'key' in kvargs:
      namekey = kvargs['key']
      dot = get_cmd.find( self._data_dict['get'] )      
      self._encode_namekey( get_cmd, dot, namekey )
      if 'get_fields' in self._data_dict:
        self._encode_getfields( get_cmd, dot )

    self._get_cmd = get_cmd   # for debug purposes

    # retrieve the XML configuration
    self.xml = self.D.rpc.get_config( get_cmd )

    # return self for call-chaining, yo!
    return self

  ### -------------------------------------------------------------------------
  ### keys - return Table data item keys (list)
  ### -------------------------------------------------------------------------

  def _keys_composite(self, xpath, key_list):
    """ composite keys return a tuple of key-items """
    _tkey = lambda this: tuple([this.findtext(k) for k in key_list ])
    return [_tkey(item) for item in self.xml.xpath(xpath)]

  def keys(self ):
    """ return a list of data item keys from the Table XML """
    key_value = self._data_dict.get('key','name')
    xpath = self._data_dict['get']

    if isinstance(key_value, str):
      xpath +=  "/" + key_value
      return [x.text.strip() for x in self.xml.xpath(xpath)]

    if not isinstance( key_value, list ): 
      raise RuntimeError("What to do with key, table:'%'" % self.__class__.__name__)

    # ok, so it's a list, which means we need to extract tuple values
    return self._keys_composite( xpath, key_value )