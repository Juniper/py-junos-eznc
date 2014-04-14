# 3rd-party
from lxml import etree
from lxml.builder import E

# package modules
from jnpr.junos import jxml as JXML
from jnpr.junos.cfg.resource import Resource, P_JUNOS_EXISTS, P_JUNOS_ACTIVE


class TemplateResource(Resource):

    # -----------------------------------------------------------------------
    # PROPERTIES
    # -----------------------------------------------------------------------

    @property
    def active(self):
        """
          returns :True: if every named element in the XML is active
          returns :False: otherwise
        """
        _active = True

        for name in self._name:
            if not self.has[P_JUNOS_ACTIVE + '_' + name]:
                _active = False
                break

        return _active

    @property
    def exists(self):
        """
          returns :True: if every named element in the XML exists
          returns :False: otherwise
        """
        _exists = True

        for name in self._name:
            if not self.has[P_JUNOS_EXISTS + '_' + name]:
                _exists = False
                break

        return _exists

    # -------------------------------------------------------------------------
    # activate
    # -------------------------------------------------------------------------

    def activate(self, **kvargs):
        """
          write config to activate resource; i.e. "activate ..."
        """
        #! removed check on active due to multi-key template
        #@@@ revisit

        names = kvargs if len(kvargs) else self._name

        xml = self._xml_template_active(JXML.ACTIVATE, names)
        rsp = self._r_config_write_xml(xml)

        for name in names:
            self.has[P_JUNOS_ACTIVE + '_' + name] = True

        return True

    # -------------------------------------------------------------------------
    # deactivate
    # -------------------------------------------------------------------------

    def deactivate(self, **kvargs):
        """
          write config to deactivate resource, i.e. "deactivate ..."
        """
        #! removed check on active due to multi-key template
        #@@@ revisit

        names = kvargs if len(kvargs) else self._name

        xml = self._xml_template_active(JXML.DEACTIVATE, names)
        rsp = self._r_config_write_xml(xml)

        for name in names:
            self.has[P_JUNOS_ACTIVE + '_' + name] = False

        return True

    # -------------------------------------------------------------------------
    # delete
    # -------------------------------------------------------------------------

    def delete(self, **kvargs):
        """
          remove configuration from Junos device
        """
        # ! removed check on exists due to multi-key template
        # ! @@ revisit

        names = kvargs if len(kvargs) else self._name

        xml = self._xml_template_delete(names)
        rsp = self._r_config_write_xml(xml)

        for name in names:
            self.has[P_JUNOS_EXISTS + '_' + name] = False

        return True

    # -------------------------------------------------------------------------
    # rename
    # -------------------------------------------------------------------------

    def rename(self, new_name=None, **kvargs):
        """
          Not supported (for now) - raise RuntimeError
        """
        raise RuntimeError(
            "rename not supported on %s" %
            self.__class__.__name__)

    # -------------------------------------------------------------------------
    # reorder
    # -------------------------------------------------------------------------

    def reorder(self, **kvargs):
        """
          Not supported - raises RuntimeError
        """
        raise RuntimeError(
            "reorder not supported on %s" %
            self.__class__.__name__)

    # -----------------------------------------------------------------------
    # ~private~ OVERLOADING
    # -----------------------------------------------------------------------

    def _r_config_read_xml(self):
        """
        ~! OVERLOADS :Resource: !~
          read the resource config from the Junos device
        """
        return self._junos.rpc.get_config(self._xml_template_read())

    def _xml_build_change(self):
        """
        ~! OVERLOADS :Resource !~
          run the templater to produce the XML for change.  this
          method is invoked by the parent :Resource: during the
          invocation of the :write():
        """
        return self._xml_template_write()

    # -----------------------------------------------------------------------
    # ~private~ resource helper methods
    # -----------------------------------------------------------------------

    def _r_has_init(self):
        """
          initializes the :has: attribute
        """
        self.has.clear()
        for name in self._name:
            self.has[P_JUNOS_EXISTS + '_' + name] = False
            self.has[P_JUNOS_ACTIVE + '_' + name] = False

    def _r_set_active(self, my_props, value):
        """
          sets each of the :has: name P_JUNOS_ACTIVE
          properties to :value:
        """
        for name in self._name:
            my_props[P_JUNOS_ACTIVE + '_' + name] = value

    def _r_set_exists(self, my_props, value):
        """
          sets each of the name P_JUNOS_ACTIVE
          properties to in the :my_props: to :value:
        """
        for name in self._name:
            my_props[P_JUNOS_EXISTS + '_' + name] = value

    def _r_has_xml_status(self, xml_ele, to_py):
        """
          set the P_JUNOS_EXISTS and P_JUNOS_ACTIVE property
          states for each item in the resource name as extracted
          from the XML configuration retrieved from the Junos device
        """
        for name in self._xpath_names:
            if xml_ele[name] is not None:
                to_py[P_JUNOS_EXISTS + '_' + name] = True
                active = False if 'inactive' in xml_ele[name].attrib else True
                to_py[P_JUNOS_ACTIVE + '_' + name] = active
            else:
                to_py[P_JUNOS_EXISTS + '_' + name] = False
                to_py[P_JUNOS_ACTIVE + '_' + name] = False

    def _r_template_write_vars(self):
        """
          This method is called when the XML config-write template
          is being formed.  by default the simplest case is to combine
          all of the variables together.  more complicated template
          resources can overload this method to do what they want.
        """
        t_vars = dict(self._name)
        t_vars.update(self.has)
        t_vars.update(self.should)
        return t_vars

    # -----------------------------------------------------------------------
    # ~private~ methods used to create XML structures from templates
    # -----------------------------------------------------------------------

    def _xml_template_active(self, cmd, names):
        """
          create an XML structure that will activate/deactivate
          the named elements in the resource configuration
        """

        xml = self._xml_template_names_only()
        for name, xpath in self._xpath_names.items():
            if name not in names:
                continue
            ele = xml.find(xpath)
            ele.attrib.update(cmd)
        return xml

    def _xml_template_delete(self, names):
        """
          creates an XML structure that will delete
          the named elements in the resource configuration
        """

        xml = self._xml_template_names_only()
        for name, xpath in self._xpath_names.items():
            if name not in names:
                continue
            ele = xml.find(xpath)
            ele.attrib.update(JXML.DEL)
        return xml

    def _xml_template_read(self):
        """
          create an XML structure from template that
          will be used to read the resource configuration
          from the Junos device
        """
        t = self._j2_ldr.get_template(self._j2_rd)
        return etree.XML(t.render(self._name))

    def _xml_template_names_only(self):
        """
          create an XML structure from template that will
          be used to read only the resource name values
          from the Junos device
        """
        t = self._j2_ldr.get_template(self._j2_rd)
        return etree.XML(t.render(self._name, NAMES_ONLY=True))

    def _xml_template_write(self):
        t_vars = self._r_template_write_vars()
        t = self._j2_ldr.get_template(self._j2_wr)
        return etree.XML(t.render(t_vars))
