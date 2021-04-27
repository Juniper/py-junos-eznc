# stdlib
from pprint import pformat
from copy import deepcopy

# 3rd-party
from lxml.builder import E

# package modules
from jnpr.junos import jxml as JXML

P_JUNOS_EXISTS = "_exists"
P_JUNOS_ACTIVE = "_active"


class Resource(object):

    PROPERTIES = [P_JUNOS_EXISTS, P_JUNOS_ACTIVE]

    def __init__(self, junos, namevar=None, **kvargs):
        """
        Resource or Resource-Manager constructor.  All managed resources
        and resource-managers inherit from this class.

        junos
          Instance of Device, this is bound to the Resource for
          device access

        namevar
          If not None, identifies a specific resource by 'name'.  The
          format of the name is resource dependent.  Most resources take
          a single string name, while others use tuples for compound names.
          refer to each resource for the 'namevar' definition

          If namevar is None, then the instance is a Resource-Manager (RM).
          The RM is then used to select specific resources by name using
          the __getitem__ overload.

        kvargs['P'] or kvargs['parent']
          Instance to the resource parent.  This is set when resources have
          hierarchical relationships, like rules within rulesets

        kvargs['M']
          Instance to the resource manager.
        """
        self._junos = junos
        self._name = namevar
        self._parent = kvargs.get("parent") or kvargs.get("P")
        self._opts = kvargs
        self._manager = kvargs.get("M")

        if not namevar:
            # then this is a resource-manager instance. setup the list and
            # catalog attributes, but do not load them now.  when the caller
            # invokes the properties, they will auto-load when empty.
            self._rlist = []
            self._rcatalog = {}
            return

        # otherwise, a resource includes public attributes:

        self.properties = []
        self.properties.extend(Resource.PROPERTIES)
        if self.__class__ != Resource:
            self.properties.extend(self.__class__.PROPERTIES)

        # if this resource manages others, then hook that
        # into the :manages: list

        if hasattr(self, "MANAGES"):
            self._manages = self.MANAGES.keys()
            for k, v in self.MANAGES.items():
                self.__dict__[k] = v(junos, parent=self)

        # setup resource cache-attributes

        self.has = {}
        self.should = {}
        self._is_new = False

        # now load the properties from the device.
        self.read()

    # -----------------------------------------------------------------------
    # PROPERTIES
    # -----------------------------------------------------------------------

    @property
    def active(self):
        """
        is this resource configuration active on the Junos device?

        :RuntimeError: if invoked on a manager object
        """
        if self.is_mgr:
            raise RuntimeError("Not on a manager!")
        return self.has[P_JUNOS_ACTIVE]

    @property
    def exists(self):
        """
        does this resource configuration exist on the Junos device?

        :RuntimError: if invoked on a manager
        """
        if self.is_mgr:
            raise RuntimeError("Not on a manager!")
        return self.has[P_JUNOS_EXISTS]

    @property
    def is_mgr(self):
        """
        is this a resource manager?
        """
        return self._name is None

    @property
    def is_new(self):
        """
        is this a new resource? that is, it does not exist
        on the Junos device when it was initally retrieved

        :RuntimeError: if invoked on a manager
        """
        if self.is_mgr:
            raise RuntimeError("Not on a manager!")
        return self._is_new

    @property
    def name(self):
        """
        the name of the resource

        :RuntimeError: if invoked on a manager
        """
        if self.is_mgr:
            raise RuntimeError("Not on a manager!")
        return self._name

    @name.setter
    def name(self, value):
        if self.is_mgr:
            raise RuntimeError("Not on a manager!")
        raise AttributeError("name is currently read-only")

    @property
    def manages(self):
        """
        a resource may contain sub-managers for hierarchical
        oriented resources.  this method will return a list
        of manager names attached to this resource, or
        :None: if there are not any
        """
        if hasattr(self, "_manages"):
            return self._manages
        return None

    @manages.setter
    def manages(self):
        raise AttributeError("read-only")

    @property
    def xml(self):
        """
        for debugging the resource XML configuration that was
        read from the Junos device
        """
        if self.is_mgr:
            raise RuntimeError("Not on a manager!")
        return self._has_xml

    @property
    def list(self):
        """
        returns a list of named resources
        """
        if not self.is_mgr:
            raise RuntimeError("Must be a manager!")
        if not len(self._rlist):
            self.list_refresh()
        return self._rlist

    @property
    def catalog(self):
        """
        returns a dictionary of resources
        """
        if not self.is_mgr:
            raise RuntimeError("Must be a manager!")
        if not len(self._rcatalog):
            self.catalog_refresh()
        return self._rcatalog

    # -------------------------------------------------------------------------
    # shortcuts
    # -------------------------------------------------------------------------

    @property
    def D(self):
        """returns the Device object bound to this resource/manager"""
        return self._junos

    @property
    def R(self):
        """returns the Device RPC meta object"""
        return self._junos.rpc

    @property
    def M(self):
        """returns the :Resource: manager associated to this resource"""
        return self._manager

    @property
    def P(self):
        """returns the parent of the associated Junos object"""
        return self._parent

    # -----------------------------------------------------------------------
    # PUBLIC METHODS
    # -----------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # read
    # -------------------------------------------------------------------------

    def read(self):
        """
        read resource configuration from device
        """

        self._r_has_init()
        self._has_xml = self._r_config_read_xml()

        if self._has_xml is None or not len(self._has_xml):
            self._is_new = True
            self._r_when_new()
            return None

        # the xml_read_parser *MUST* be implement by the
        # resource subclass.  it is used to parse the XML
        # into native python structures.

        self._xml_to_py(self._has_xml, self.has)

        # return the python structure represntation
        return True

    # -------------------------------------------------------------------------
    # write
    # -------------------------------------------------------------------------

    def write(self, **kvargs):
        """
        write resource configuration stored in :should: back to device

        kvargs['touch']
          if True, then write() will skip the check to see if any
          items exist in :should:
        """
        if self.is_mgr:
            raise RuntimeError("Not on a manager!")

        if not len(self.should) and "touch" not in kvargs:
            return False

        # if this resource did not previously exist,
        # then mark it now into :should:

        if P_JUNOS_EXISTS not in self.should:
            self._r_set_exists(self.should, True)

        if self.is_new:
            self._r_set_active(self.should, True)

        # construct the XML change structure
        xml_change = self._xml_build_change()
        if xml_change is None:
            return False

        # write these changes to the device
        self._r_config_write_xml(xml_change)

        # copy :should: into :has: and then clear :should:
        self.has.update(self.should)
        self.should.clear()

        return True

    # -------------------------------------------------------------------------
    # activate
    # -------------------------------------------------------------------------

    def activate(self):
        """
        activate resource in Junos config
        the same as the Junos config-mode "activate" command
        """
        # no action needed if it's already active
        if self.active:
            return False
        self._r_set_active(self.should, True)
        return self.write()

    # -------------------------------------------------------------------------
    # deactivate
    # -------------------------------------------------------------------------

    def deactivate(self):
        """
        activate resource in Junos config
        the same as the Junos config-mode "deactivate" command
        """
        # no action needed if it's already deactive
        if not self.active:
            return False
        self._r_set_active(self.should, False)
        return self.write()

    # -------------------------------------------------------------------------
    # delete
    # -------------------------------------------------------------------------

    def delete(self):
        """
        remove configuration from Junos device
        the same as the Junos config-mode "delete" command
        """
        # cannot delete something that doesn't exist
        # @@@ should raise?

        if not self.exists:
            return False

        # remove the config from Junos
        xml = self._xml_edit_at_res()
        xml.attrib.update(JXML.DEL)
        self._xml_hook_on_delete(xml)
        self._r_config_write_xml(xml)

        # reset the :has: attribute
        self._r_has_init()
        return True

    # -------------------------------------------------------------------------
    # rename
    # -------------------------------------------------------------------------

    def rename(self, new_name):
        """
        rename resource in Junos configuration
        the same as the Junos config-mode "rename" command
        """
        # cannot rename something that doesn't exist
        # @@@ should raise?

        if not self.exists:
            return False

        xml = self._xml_edit_at_res()
        xml.attrib.update(JXML.REN)
        xml.attrib.update(JXML.NAME(new_name))

        self._r_config_write_xml(xml)
        self._name = new_name

        return True

    # -------------------------------------------------------------------------
    # reorder
    # -------------------------------------------------------------------------

    def reorder(self, **kvargs):
        """
        move the configuration within the Junos hierarcy
        the same as the Junos config-mode "insert" command

        :kvargs:
          after="<name>"
          before="<name>"
        """
        cmd, name = next(kvargs.iteritems())
        if cmd != "before" and cmd != "after":
            raise ValueError("Must be either 'before' or 'after'")

        xml = self._xml_edit_at_res()
        xml.attrib.update(JXML.INSERT(cmd))
        xml.attrib.update(JXML.NAME(name))

        self._r_config_write_xml(xml)
        return True

    def list_refresh(self):
        """
        reloads the managed resource list from the Junos device
        """
        if not self.is_mgr:
            raise RuntimeError("Only on a manager!")
        del self._rlist[:]
        self._r_list()  # invoke the specific resource method

    def catalog_refresh(self):
        """
        reloads the resource catalog from the Junos device
        """
        if not self.is_mgr:
            raise RuntimeError("Only on a manager!")
        self._rcatalog.clear()
        self._r_catalog()  # invoke the specific resource method

    def _r_catalog(self):
        """
        provide a 'default' catalog creator method that simply uses
        the manager list and runs through each resource making
        a refcopy to the :has: properties
        """
        zone_list = self.list
        for name in zone_list:
            r = self[name]
            self._rcatalog[name] = r.has

    def refresh(self):
        if not self.is_mgr:
            raise RuntimeError("Only on a manager!")
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

    # -----------------------------------------------------------------------
    # OVERLOADS
    # -----------------------------------------------------------------------

    # ---------------------------------------------------------------------
    # ITEMS: for read/write of resource managed properties
    # ---------------------------------------------------------------------

    def __getitem__(self, namekey):
        """
        implements [] to obtain property value.  value will come
        from :should: if set or from :has: otherwise.
        """

        if self.is_mgr:
            # ---------------------------------------------------------------
            # use is resource-manager accessing specific index/name
            # to return resource instance
            # ---------------------------------------------------------------

            self._opts["M"] = self
            if isinstance(namekey, int):
                # index, not name
                namekey = self.list[namekey]

            res = self.__class__(self._junos, namekey, **self._opts)
            return res

        # ---------------------------------------------------------------
        # use-case is resource instance for read property
        # ---------------------------------------------------------------

        if namekey in self.should:
            return self.should[namekey]

        if namekey in self.has:
            return self.has[namekey]

        if namekey in self.properties:
            # it's a valid property, just not set in the resource
            return None

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

    def __call__(self, **kvargs):
        """
        alternative way to set property values as aggregation of
        key/value pairs.  this will automatically call :write():
        when completed.
        """
        if self.is_mgr:
            raise RuntimeError("Not on a manager!")
        if not kvargs:
            return False

        # validate property names first!
        for p_name, p_val in kvargs.items():
            if p_name not in self.properties:
                raise ValueError("Unknown property: %s" % p_name)

        # now cleared to add all the values
        self.should.update(kvargs)
        return self.write()

        # ---------------------------------------------------------------------
        # ATTRIBUTE: for read/write of resource managed properties
        # ---------------------------------------------------------------------

    def __getattr__(self, namekey):
        """
        returns property value, accessed as attribute <resource>.<property>
        only for resource instance
        """
        if self.is_mgr:
            raise RuntimeError("not on a resource-manager")
        return self[namekey]

    def __setattr__(self, name, value):
        if hasattr(self, "properties") and name in self.properties:
            # we can set this name/value in the resource property
            self[name] = value
        else:
            # pass 'up' to standard setattr method
            object.__setattr__(self, name, value)

        # ---------------------------------------------------------------------
        # PRINT/DEBUG
        # ---------------------------------------------------------------------

    def __repr__(self):
        """
        stringify for debug/printing

        this will show the resource manager (class) name,
        the resource (Junos) name, and the contents
        of the :has: dict and the contents of the :should: dict
        """
        mgr_name = self.__class__.__name__
        return (
            "NAME: %s: %s\nHAS: %s\nSHOULD:%s"
            % (mgr_name, self._name, pformat(self.has), pformat(self.should))
            if not self.is_mgr
            else "Resource Manager: %s" % mgr_name
        )

        # ---------------------------------------------------------------------
        # ITERATOR
        # ---------------------------------------------------------------------

    def __iter__(self):
        """iterate through each Resource in the Manager list"""
        for name in self.list:
            yield self[name]

    # -----------------------------------------------------------------------
    # XML reading
    # -----------------------------------------------------------------------

    def _r_config_read_xml(self):
        """
        read the resource config from the Junos device
        """
        get = self._xml_at_top()
        self._xml_hook_read_begin(get)
        got = self._junos.rpc.get_config(get)
        return self._xml_at_res(got)

    def _xml_at_top(self):
        """
        ~| WARNING |~
        resource subclass *MUST* implement this!

        Create an XML structure that will be used to retrieve
        the resource configuration from the device.
        """
        raise RuntimeError("Resource missing method: %s" % self.__class__.__name__)

    def _xml_at_res(self, xml):
        """
        ~| WARNING |~
        resource subclass *MUST* implement this!

        Return the XML element of the specific resource from
        the :xml: structure.  The :xml: will be the configuration
        starting at the top of the Junos config, i.e.
        <configuration>, and the resource needs to "cursor" at
        the specific resource within that structure
        """
        raise RuntimeError("Resource missing method: %s" % self.__class__.__name__)

    # -----------------------------------------------------------------------
    # XML writing
    # -----------------------------------------------------------------------

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

        self._xml_hook_build_change_begin(edit_xml)

        # if this resource should be deleted then
        # handle that case and return

        if not self.should[P_JUNOS_EXISTS]:
            self._xml_change__exists(edit_xml)
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

        changed |= self._xml_hook_build_change_end(edit_xml)

        return edit_xml if changed else None

    def _r_config_write_xml(self, xml):
        """
        write the xml change to the Junos device,
        trapping on exceptions.
        """
        top_xml = xml.getroottree().getroot()

        try:
            result = self._junos.rpc.load_config(top_xml, action="replace")
        except Exception as err:
            # see if this is OK or just a warning
            if len(err.rsp.xpath('.//error-severity[. = "error"]')):
                raise err
            return err.rsp

        return result

    # ------------------------------------------------------------------------
    # XML edit cursor methods
    # ------------------------------------------------------------------------

    def _xml_edit_at_res(self):
        return self._xml_at_res(self._xml_at_top())

    # ------------------------------------------------------------------------
    # XML standard properties "writers"
    # ------------------------------------------------------------------------

    def _xml_change_description(self, xml):
        Resource.xml_set_or_delete(xml, "description", self.should["description"])
        return True

    def _xml_change__active(self, xml):
        if self.should[P_JUNOS_ACTIVE] == self.has[P_JUNOS_ACTIVE]:
            return False
        value = "active" if self.should[P_JUNOS_ACTIVE] else "inactive"
        xml.attrib[value] = value
        return True

    def _xml_change__exists(self, xml):
        # if this is a change to create something new,
        # then invoke the 'on-create' hook and return
        # the results

        if self.should[P_JUNOS_EXISTS]:
            return self._xml_hook_on_new(xml)

        # otherwise, we are deleting this resource
        xml.attrib.update(JXML.DEL)

        # now call the 'on-delete' hook and return
        # the results

        return self._xml_hook_on_delete(xml)

    # -----------------------------------------------------------------------
    # XML HOOK methods
    # -----------------------------------------------------------------------

    def _xml_hook_read_begin(self, xml):
        """
        called from :_r_config_read_xml(): after call to :_xml_at_top(): and
        before the config request is made to the Junos device.  This hook
        allows the subclass to munge the XML get-request with additional items
        if necessary

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

    def _xml_hook_on_delete(self, xml):
        """
        called when an XML write operation is going to delete the resource.

        Returns:
          :True: when :xml: is changed
          :False: otherwise
        """
        return False

    def _xml_hook_on_new(self, xml):
        """
        called when an XML write operation is going to create a new resource.

        Returns:
          :True: when :xml: is changed
          :False: otherwise
        """
        return False

    # -----------------------------------------------------------------------
    # Resource HOOK methods
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # ~private~ resource methods
    # -----------------------------------------------------------------------

    def _r_set_active(self, my_props, value):
        my_props[P_JUNOS_ACTIVE] = value

    def _r_set_exists(self, my_props, value):
        my_props[P_JUNOS_EXISTS] = value

    def _r_has_init(self):
        self.has.clear()
        self.has[P_JUNOS_EXISTS] = False
        self.has[P_JUNOS_ACTIVE] = False

    @classmethod
    def _r_has_xml_status(klass, as_xml, as_py):
        """
        set the 'exists' and 'active' :has: values
        """
        as_py[P_JUNOS_ACTIVE] = False if as_xml.attrib.get("inactive") else True
        as_py[P_JUNOS_EXISTS] = True

    @classmethod
    def xml_set_or_delete(klass, xml, ele_name, value):
        """
        HELPER function to either set a value or remove the element
        """
        if value is not None and not isinstance(value, str):
            value = str(value)
        xml.append(E(ele_name, (value if value else JXML.DEL)))

    @classmethod
    def xmltag_set_or_del(klass, ele_name, value):
        """
        HELPER function creates an XML element tag read-only
        that includes the DEL attribute depending on :value:
        """
        return E(ele_name, ({} if value else JXML.DEL))

    @classmethod
    def copyifexists(klass, xml, ele_name, to_py, py_name=None):
        ele_val = xml.find(ele_name)
        if ele_val is not None:
            to_py[(py_name if py_name else ele_name)] = ele_val.text.strip()

    @classmethod
    def diff_list(klass, has_list, should_list):
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
        (adds, dels) = Resource.diff_list(
            self.has.get(prop_name, []), self.should[prop_name]
        )
        for this in adds:
            xml.append(E(element_name, E.name(this)))
        for this in dels:
            xml.append(E(element_name, JXML.DEL, E.name(this)))
