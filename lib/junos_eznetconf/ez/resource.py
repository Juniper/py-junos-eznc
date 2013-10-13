import pdb
from lxml.builder import E 

P_JUNOS_EXISTS = '_exists'
P_JUNOS_ACTIVE = '_active'

class EzResource(object):

  PROPERTIES = [
    P_JUNOS_EXISTS,
    P_JUNOS_ACTIVE
  ]

  def __init__(self, junos, namekey=None, **kvargs ):
    self._junos = junos
    self._name = namekey
    self._parent = kvargs.get('parent')
    self._opts = kvargs

    # resource manager list and catalog
    self._rlist = None
    self._rcatalog = None

    # if we are creating the manager, i.e. not a specific named item,
    # then return now.

    if not namekey: return

    # otherwise, a resource includes attributes to manage the :has: and
    # :should: property information

    self.has = {}
    self.should = {}

  def read(self):
    """
      read resource configuration from device
    """

    self.has.clear()
    cfg_xml = self._xml_config_read()
    self._has_xml = self._xml_get_has_xml( cfg_xml )

    # if the resource does not exist in Junos, then mark
    # the :has: accordingly and invoke :_init_has: for any
    # defaults

    if None == self._has_xml:
      self.has[P_JUNOS_EXISTS] = False
      self.has[P_JUNOS_ACTIVE] = False
      self._init_has()
      return None

    # the xml_read_parser *MUST* be implement by the 
    # resource subclass.  it is used to parse the XML
    # into native python structures.

    self._xml_read_parser( self._has_xml, self.has )

    # return the python structure represntation
    return self.has

  def write(self):
    """
      write resource configuration to device
    """
    return True

  def __getitem__( self, namekey ):
    """
      implements []
    """
    if self.is_mgr:      
      return self._select( namekey )

    # if the property is already set in :should:
    # then return that before returning the value from :has:

    if self.should.get(namekey): return self.should[namekey]
    if self.has.get(namekey):    return self.has[namekey]

    raise ValueError("Unknown property request: %s" % namekey)

  def __setitem__(self, r_prop, value):
    """
      implements []=
    """
    if self.is_mgr: 
      raise RuntimeError("Not on a manager!")
    if r_prop in self.properties:
      self.should[r_prop] = value
    else:
      raise ValueError("Uknown property request: %s" % r_prop)

  def __repr__(self):
    """
      stringify for debug/printing
    """
    iam = self.__class__.__name__
    return "%s: %s" % (iam, self._name) if not self.is_mgr \
      else "Resource Manager: %s" % iam

  @property
  def is_mgr(self):
    """
      is this a resource manager?
    """    
    return (self._name == None)
  
  @property
  def exists(self):
    """
      does this resource configuration exist?
    """
    if self.is_mgr: raise RuntimeError("Not on a manager!")
    return self.has[P_JUNOS_EXISTS]

  @property
  def active(self):
    """
      is this configuration active?
    """
    if self.is_mgr: raise RuntimeError("Not on a manager!")
    return self.has[P_JUNOS_ACTIVE]
    
  @active.setter
  def active(self, value):
    """
      mark the resource for activate/deactivate
    """
    if self.is_mgr: raise RuntimeError("Not on a manager!")
    if not isinstance(value,bool): raise ValueError("value must be True/False")
    self.should[P_JUNOS_ACTIVE] = value

  ##### -----------------------------------------------------------------------
  ##### resource subclass helper methods
  ##### -----------------------------------------------------------------------

  def _set_ea_status( self, as_xml, as_py ):
    """
      set the 'exists' and 'active' :has: values
    """
    as_py[P_JUNOS_ACTIVE] = False if as_xml.attrib.get('inactive') else True
    as_py[P_JUNOS_EXISTS] = True

  ##### -----------------------------------------------------------------------
  ##### abstract methods
  ##### -----------------------------------------------------------------------

  def _select( self, namekey ):
    if not self.is_mgr:
      raise RuntimeError("This is not a reosurce manager")
    res = self.__class__( self._junos, namekey, **self._opts )
    res.read()
    return res

  def _xml_config_read(self):
    return self._junos.rpc.get_config( self._xml_at_top() )

  ##### -----------------------------------------------------------------------
  ##### abstract pass methods
  ##### -----------------------------------------------------------------------

  def _init_has( self ): pass
  def _xml_get_has_xml( self, xml ): pass

