import pdb

# stdlib
from pprint import pformat
from copy import deepcopy

# 3rd-party
from lxml.builder import E 

# package modules
from .. import jxml as JXML

P_JUNOS_EXISTS = '_exists'
P_JUNOS_ACTIVE = '_active'

class Resource(object):

  PROPERTIES = [
    P_JUNOS_EXISTS,
    P_JUNOS_ACTIVE
  ]

  def __init__(self, junos, namekey=None, **kvargs ):
    self._junos = junos
    self._name = namekey
    self._parent = kvargs.get('parent')
    self._opts = kvargs
    self._manager = kvargs.get('M')

    # resource manager list and catalog
    self._rlist = []
    self._rcatalog = {}

    # if we are creating the manager, i.e. not a specific named item,
    # then return now.

    if not namekey: return

    # otherwise, a resource includes public attributes:

    self.properties = []
    self.properties.extend(Resource.PROPERTIES)
    if self.__class__ != Resource: 
      self.properties.extend(self.__class__.PROPERTIES)

    self.has = {}
    self.should = {}
    self._is_new = False

  ##### -----------------------------------------------------------------------
  ##### PROPERTIES
  ##### -----------------------------------------------------------------------

  @property
  def active(self):
    """
    is this resource configuration active on the Junos device?

    :RuntimeError: if invoked on a manager object
    """
    if self.is_mgr: raise RuntimeError("Not on a manager!")    
    return self.has[P_JUNOS_ACTIVE]

  @property
  def exists(self):
    """
    does this resource configuration exist on the Junos device?

    :RuntimError: if invoked on a manager
    """
    if self.is_mgr: raise RuntimeError("Not on a manager!")    
    return self.has[P_JUNOS_EXISTS]

  @property
  def is_mgr(self):
    """
    is this a resource manager?
    """    
    return (self._name == None)

  @property
  def is_new(self):
    """
    is this a new resource? that is, it does not exist
    on the Junos device when it was initally retrieved

    :RuntimeError: if invoked on a manager
    """
    if self.is_mgr: raise RuntimeError("Not on a manager!")    
    return self._is_new

  @property
  def name(self):
    """
    the name of the resource
    
    :RuntimeError: if invoked on a manager
    """
    if self.is_mgr: raise RuntimeError("Not on a manager!")    
    return self._name

  @name.setter
  def name(self, value):
    if self.is_mgr: raise RuntimeError("Not on a manager!")        
    raise AttributeError("name is currently read-only")
  
  @property
  def manages(self):
    """
    a resource may contain sub-managers for hierarchical
    oriented resources.  this method will return a list
    of manager names attached to this resource, or 
    :None: if there are not any
    """
    if hasattr(self,'_manages'): return self._manages
    return None

  @manages.setter
  def manages (self):
    raise AttributeError("read-only")

  @property
  def xml(self):
    """
    for debugging the resource XML configuration that was
    read from the Junos device
    """
    if self.is_mgr: raise RuntimeError("Not on a manager!")        
    return self._has_xml

  @property
  def list(self):
    """
    returns a list of named resources
    """
    if not self.is_mgr: raise RuntimeError("Must be a manager!")
    if not len(self._rlist): self.list_refresh()
    return self._rlist

  @property
  def catalog(self):
    """
      returns a dictionary of resources
    """
    if not self.is_mgr: raise RuntimeError("Must be a manager!")
    if not len(self._rcatalog): self.catalog_refresh()
    return self._rcatalog

  ### -------------------------------------------------------------------------
  ### shortcuts
  ### -------------------------------------------------------------------------

  @property
  def J(self):
    """
    returns the Junos object associated to this resource/manager
    """
    return self._junos

  @property
  def M(self):
    """
    returns the :Resource: manager associated to this resource
    """
    return self._manager

  @property
  def E(self):
    """
    returns the :ez: attribute of the associated Junos object
    """
    return self._junos.ez
  
  @property
  def P(self):
    """
    returns the parent of the associated Junos object
    """
    return self._parent

  ##### -----------------------------------------------------------------------
  ##### PUBLIC METHODS
  ##### -----------------------------------------------------------------------

  ### -------------------------------------------------------------------------
  ### read
  ### -------------------------------------------------------------------------

  def read(self):
    """
    read resource configuration from device
    """

    self._r_has_init()
    self._has_xml =  self._r_config_read_xml()

    if None == self._has_xml or not len(self._has_xml):
      self._is_new = True
      self._r_when_new()
      return None

    # the xml_read_parser *MUST* be implement by the 
    # resource subclass.  it is used to parse the XML
    # into native python structures.

    self._xml_to_py( self._has_xml, self.has )

    # return the python structure represntation
    return True

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

    # if this resource did not previously exist,
    # then mark it now into :should:

    if not self.should.has_key(P_JUNOS_EXISTS): 
      self._r_set_exists( self.should, True )

    if self.is_new:
      self._r_set_active( self.should, True )

    # construct the XML change structure
    xml_change = self._xml_build_change()
    if None == xml_change: return False

    # write these changes to the device
    rsp = self._r_config_write_xml( xml_change )

    # copy :should: into :has: and then clear :should:
    self.has.update( self.should )
    self.should.clear()

    return True

  ### -------------------------------------------------------------------------
  ### activate
  ### -------------------------------------------------------------------------

  def activate(self):
    """
    activate resource in Junos config
    the same as the Junos config-mode "activate" command
    """
    # no action needed if it's already active 
    if self.active: return False
    self._r_set_active( self.should, True )
    return self.write()

  ### -------------------------------------------------------------------------
  ### deactivate
  ### -------------------------------------------------------------------------

  def deactivate(self):
    """
    activate resource in Junos config
    the same as the Junos config-mode "deactivate" command
    """
    # no action needed if it's already deactive
    if not self.active: return False
    self._r_set_active( self.should, False)
    return self.write()

  ### -------------------------------------------------------------------------
  ### delete
  ### -------------------------------------------------------------------------

  def delete(self):
    """
    remove configuration from Junos device
    the same as the Junos config-mode "delete" command
    """
    # cannot delete something that doesn't exist
    # @@@ should raise?

    if not self.exists: return False

    # remove the config from Junos
    xml = self._xml_edit_at_res()
    xml.attrib.update( JXML.DEL )
    self._xml_hook_on_delete( xml )
    rsp = self._r_config_write_xml( xml )

    # reset the :has: attribute
    self._r_has_init()
    return True

  ### -------------------------------------------------------------------------
  ### rename
  ### -------------------------------------------------------------------------

  def rename(self, new_name):
    """
    rename resource in Junos configuration
    the same as the Junos config-mode "rename" command
    """
    # cannot rename something that doesn't exist
    # @@@ should raise?

    if not self.exists: return False

    xml = self._xml_edit_at_res()
    xml.attrib.update( JXML.REN )
    xml.attrib.update( JXML.NAME( new_name ))

    rsp = self._r_config_write_xml( xml )
    self._name = new_name

    return True

  ### -------------------------------------------------------------------------
  ### reorder
  ### -------------------------------------------------------------------------

  def reorder( self, **kvargs ):
    """
    move the configuration within the Junos hierarcy
    the same as the Junos config-mode "insert" command

    :kvargs: 
      after="<name>"
      before="<name>"
    """
    cmd, name = next(kvargs.iteritems())
    if cmd != 'before' and cmd != 'after':
      raise ValueError("Must be either 'before' or 'after'")

    xml = self._xml_edit_at_res()
    xml.attrib.update( JXML.INSERT( cmd ))
    xml.attrib.update( JXML.NAME( name ))

    rsp = self._r_config_write_xml( xml )
    return True

  def list_refresh(self):
    """
    reloads the managed resource list from the Junos device
    """
    del self._rlist[:]
    self._r_list()      # invoke the specific resource method

  def catalog_refresh(self):
    """
      reloads the resource catalog from the Junos device
    """
    self._rcatalog.clear()
    self._r_catalog()  # invoke the specific resource method

  def refresh(self):
    self.list_refresh()
    self.catalog_refresh()
    
  def propcopy(self, p_name):
    """
    proptery from :has: to :should:

    performs a 'deepcopy' of the property; used to make
    changes to list, dict type properties
    """
    self.should[p_name] = deepcopy(self.has[p_name])
    return self.should[p_name]

  ##### -----------------------------------------------------------------------
  ##### OPERATOR OVERLOADING
  ##### -----------------------------------------------------------------------

  def __getitem__( self, namekey ):
    """
      implements [] to obtain property value.  value will come
      from :should: if set or from :has: otherwise.
    """

    if self.is_mgr: 
      self._opts['M'] = self
      res = self.__class__( self._junos, namekey, **self._opts )
      res.read()
      return res

    # if the property is already set in :should:
    # then return that before returning the value from :has:

    if self.should.get(namekey): return self.should[namekey]
    if self.has.get(namekey):    return self.has[namekey]

    raise ValueError("Unknown property request: %s" % namekey)

  def __setitem__(self, r_prop, value):
    """
      implements []= to set property value into :should:
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

      this will show the resource manager (class) name, 
      the resource (Junos) name, and the contents
      of the :has: dict and the contents of the :should: dict
    """
    mgr_name = self.__class__.__name__    
    return "NAME: %s: %s\nHAS: %s\nSHOULD:%s" % \
      (mgr_name, self._name, pformat(self.has), pformat(self.should)) \
      if not self.is_mgr \
      else "Resource Manager: %s" % mgr_name

  def __call__(self, **kvargs):
    """
      alternative way to set property values as aggregation of
      key/value pairs
    """
    if self.is_mgr: raise RuntimeError("Not on a manager!")
    if not kvargs: return False

    # validate property names first!
    for p_name,p_val in kvargs.items():
      if p_name not in self.properties:
        raise ValueError("Unknown property: %s" % p_name)

    # now cleared to add all the values
    self.should.update( kvargs )
    return True

  ##### -----------------------------------------------------------------------
  ##### XML reading 
  ##### -----------------------------------------------------------------------

  def _r_config_read_xml(self):
    """
    read the resource config from the Junos device
    """
    get = self._xml_at_top()
    self._xml_hook_read_begin( get )
    got = self._junos.rpc.get_config( get )
    return self._xml_at_res( got )

  def _xml_at_top( self ): 
    """
    ~| WARNING |~
    resource subclass *MUST* implement this!

    Create an XML structure that will be used to retrieve 
    the resource configuration from the device.
    """    
    raise RuntimeError("Resource missing method: %s" %
      self.__class__.__name__)    

  def _xml_at_res( self, xml ): 
    """
    ~| WARNING |~
    resource subclass *MUST* implement this!

    Return the XML element of the specific resource from
    the :xml: structure.  The :xml: will be the configuration
    starting at the top of the Junos config, i.e.
    <configuration>, and the resource needs to "cursor" at
    the specific resource within that structure
    """
    raise RuntimeError("Resource missing method: %s" %
      self.__class__.__name__)
  
  ##### -----------------------------------------------------------------------
  ##### XML writing
  ##### -----------------------------------------------------------------------

  def _xml_build_change(self):
    """
      iterate through the :should: properties creating the 
      necessary configuration change structure.  if there
      are no changes, then return :None:
    """
    edit_xml = self._xml_edit_at_res()

    # if there is resource hook to do something
    # before we build up the xml configuration,
    # then do that now

    self._xml_hook_build_change_begin( edit_xml )

    # if this resource should be deleted then
    # handle that case and return

    if not self.should[P_JUNOS_EXISTS]:
      self._xml_change__exists( edit_xml )
      return edit_xml

    # otherwise, this is an update, and we need to
    # construct the XML for change

    changed = False
    for r_prop in self.properties:
      if r_prop in self.should:
        edit_fn = "_xml_change_" + r_prop
        changed |= getattr(self, edit_fn)(edit_xml)

    # if there is a resource hook to do something
    # after we've run through all the property methods
    # then invoke that now

    changed |= self._xml_hook_build_change_end( edit_xml )  

    return edit_xml if changed else None

  def _r_config_write_xml(self, xml):
    """
      write the xml change to the Junos device, 
      trapping on exceptions.
    """
    top_xml = xml.getroottree().getroot()

    try:
      attrs = dict(action='replace')
      result = self._junos.rpc.load_config( top_xml, attrs )
    except Exception as err:
      # see if this is OK or just a warning
      if len(err.rsp.xpath('.//error-severity[. = "error"]')):
        raise err
      return err.rsp

    return result    

  # ---------------------------------------------------------------------------
  # XML edit cursor methods
  # ---------------------------------------------------------------------------

  def _xml_edit_at_res(self):
    return self._xml_at_res(self._xml_at_top())

  # ---------------------------------------------------------------------------
  # XML standard properties "writers"
  # ---------------------------------------------------------------------------

  def _xml_change_description(self, xml):
    Resource.xml_set_or_delete(xml, 'description', self.should['description'])
    return True

  def _xml_change__active(self, xml):
    if self.should[P_JUNOS_ACTIVE] == self.has[P_JUNOS_ACTIVE]:
      return False
    value = 'active' if self.should[P_JUNOS_ACTIVE] else 'inactive'
    xml.attrib[value] = value
    return True

  def _xml_change__exists(self, xml): 
    # if this is a change to create something new,
    # then invoke the 'on-create' hook and return 
    # the results

    if self.should[P_JUNOS_EXISTS]:
      return self._xml_hook_on_new( xml )

    # otherwise, we are deleting this resource
    xml.attrib.update( JXML.DEL )

    # now call the 'on-delete' hook and return 
    # the results

    return self._xml_hook_on_delete( xml )

  ##### -----------------------------------------------------------------------
  ##### XML HOOK methods
  ##### -----------------------------------------------------------------------

  def _xml_hook_read_begin(self, xml):
    """
    called from :_r_config_read_xml(): after call to :_xml_at_top(): and
    before the config request is made to the Junos device.  This hook allows
    the subclass to munge the XML get-request with additional items if necessary

    Returns:
      :True: when :xml: is changed
      :False: otherwise
    """
    return False

  def _xml_hook_build_change_begin(self, xml):
    """
    called from :_xml_build_change(): before the individual property 
    methods are invoked.  allows the resource to do anything, like pruning
    stub elements that were generated as part of :_xml_at_top():

    Returns:
      :True: when :xml: is changed
      :False: otherwise
    """
    return False

  def _xml_hook_build_change_end(self, xml):
    """
    called from :_xml_build_change(): after all of the properties
    methods have been processed.  

    Returns:
      :True: when :xml: is changed
      :False: otherwise
    """
    return False

  def _xml_hook_on_delete( self, xml ):
    """
    called when an XML write operation is going to delete the resource.

    Returns:
      :True: when :xml: is changed
      :False: otherwise
    """
    return False

  def _xml_hook_on_new( self, xml ): 
    """
    called when an XML write operation is going to create a new resource.

    Returns:
      :True: when :xml: is changed
      :False: otherwise
    """
    return False

  ##### -----------------------------------------------------------------------
  ##### Resource HOOK methods
  ##### -----------------------------------------------------------------------

  def _r_when_new(self): 
    """
      called by :read(): when the resource is new; i.e.
      there is no existing Junos configuration
    """
    pass

  def _r_when_delete(self):
    """
    ~| not used yet |~
    """
    pass
    
  ##### -----------------------------------------------------------------------
  ##### ~private~ resource methods
  ##### -----------------------------------------------------------------------

  def _r_set_active(self, my_props, value):
    my_props[P_JUNOS_ACTIVE] = value

  def _r_set_exists(self, my_props, value):
    my_props[P_JUNOS_EXISTS] = value

  def _r_has_init(self):
    self.has.clear()
    self.has[P_JUNOS_EXISTS] = False
    self.has[P_JUNOS_ACTIVE] = False

  @classmethod
  def _r_has_xml_status( klass, as_xml, as_py ):
    """
      set the 'exists' and 'active' :has: values
    """
    as_py[P_JUNOS_ACTIVE] = False if as_xml.attrib.get('inactive') else True
    as_py[P_JUNOS_EXISTS] = True    

  @classmethod
  def set_ea_status( klass, as_xml, as_py ):
    """
      set the 'exists' and 'active' :has: values
    """
    print "~~DEPRECIATED~~[set_ea_status]~~"
    as_py[P_JUNOS_ACTIVE] = False if as_xml.attrib.get('inactive') else True
    as_py[P_JUNOS_EXISTS] = True


  @classmethod
  def xml_set_or_delete( klass, xml, ele_name, value):
    """
      HELPER function to either set a value or remove the element
    """
    xml.append(E(ele_name,(value if value else JXML.DEL )))

  @classmethod
  def xmltag_set_or_del( klass, ele_name, value):
    """
      HELPER function creates an XML element tag read-only 
      that includes the DEL attribute depending on :value:
    """
    return E(ele_name, ({} if value else JXML.DEL ))

  @classmethod
  def copyifexists( klass, xml, ele_name, to_py, py_name=None ):
    ele_val = xml.find(ele_name)
    if ele_val != None: 
      to_py[(py_name if py_name else ele_name)] = ele_val.text.strip()

  @classmethod
  def diff_list( klass, has_list, should_list ):
    # covert lists to perform differencing
    should = set(should_list)
    has = set(has_list)

    # return lists (added, removed)
    return (list(should - has), list(has - should))  

  def _xml_list_property_add_del_names(self, xml, prop_name, element_name):
    """
    utility method use to process :list: properties.  this will add/delete
    items give the propery type and associated XML element name
    """
    (adds,dels) = Resource.diff_list( self.has.get(prop_name,[]), self.should[prop_name])
    for this in adds: xml.append(E(element_name, E.name(this)))
    for this in dels: xml.append(E(element_name, JXML.DEL, E.name(this)))    