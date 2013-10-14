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

    # otherwise, a resource includes public attributes:

    self.properties = EzResource.PROPERTIES 
    if self.__class__ != EzResource: self.properties += self.__class__.PROPERTIES
    self.has = {}
    self.should = {}

  ### -------------------------------------------------------------------------
  ### read
  ### -------------------------------------------------------------------------

  def read(self):
    """
      read resource configuration from device
    """

    self.has.clear()
    cfg_xml = self._xml_config_read()
    self._has_xml = self._xml_at_res( cfg_xml )

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

    self._xml_read_to_py( self._has_xml, self.has )

    # return the python structure represntation
    return self.has

  ### -------------------------------------------------------------------------
  ### write
  ### -------------------------------------------------------------------------

  def write(self):
    """
      write resource configuration stored in :should: back to device
    """
    if self.is_mgr: raise RuntimeError("Not on a manager!")

    # if there is nothing to write, then return False
    if not len(self.should): return False

    # if the 'exists' property is not set, then default it to True
    if not self.should.get(P_JUNOS_EXISTS):
      self.should[P_JUNOS_EXISTS] = True

    # construct the XML change structure
    xml_change = self._xml_build_change()
    if None == xml_change: return False

    # write these changes to the device
    rsp = self._xml_config_write( xml_change )

    # copy :should: into :has: and then clear :should:
    self.has.update( self.should )
    self.should.clear()

    return True

  ### -------------------------------------------------------------------------
  ### OPERATOR OVERLOADING
  ### -------------------------------------------------------------------------

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

  ### -------------------------------------------------------------------------
  ### PROPERTY ACCESSORS
  ### -------------------------------------------------------------------------

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
    """
      read the resource config from the Junos device
    """
    return self._junos.rpc.get_config( self._xml_at_top() )

  def _xml_build_change(self):
    """
      iterate through the :should: properties creating the 
      necessary configuration change structure.  if there
      are no changes, then return :None:
    """
    edit_xml = self._xml_edit_at_res()

    changed = False
    for r_prop in self.should.keys():
      edit_fn = "_xml_change_" + r_prop
      if getattr(self, edit_fn)(edit_xml):
        changed = True

    return edit_xml if changed else None

  def _xml_config_write(self, xml):
    """
      write the xml change to the Junos device, trapping
      on exceptions.
    """
    top_xml = xml.getroottree().getroot()

    try:
      attrs = dict(action='replace')
      result = self._junos.rpc.load_config( top_xml, attrs )
    except Exception as err:
      # see if this is OK or just a warning
      if None == err.rsp.find('.//ok'):
        raise err
      return err.rsp

    return result    

  # ---------------------------------------------------------------------------
  # XML edit cursor methods
  # ---------------------------------------------------------------------------

  def _xml_edit_at_res(self):
    return self._xml_at_res(self._xml_at_top())

  # ---------------------------------------------------------------------------
  # XML standard change methods
  # ---------------------------------------------------------------------------

  def _xml_change__active(self, xml):
    if self.should[P_JUNOS_ACTIVE] == self.has[P_JUNOS_ACTIVE]:
      return False
    value = 'active' if self.should[P_JUNOS_ACTIVE] else 'inactive'
    xml.attrib[value] = value
    return True

  def _xml_change__exists(self, xml): return False

  ##### -----------------------------------------------------------------------
  ##### abstract pass methods
  ##### -----------------------------------------------------------------------

  def _init_has( self ): pass
  def _xml_at_res( self, xml ): return None
  def _xml_at_top( self ): return None


