# debuggin
from lxml import etree

# 3rd-party modules
from lxml.builder import E

# module packages
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML
from jnpr.junos.cfg.srx.shared_ab_addr import SharedAddrBookAddr
from jnpr.junos.cfg.srx.shared_ab_set import SharedAddrBookSet


class SharedAddrBook(Resource):

    """
    [edit security address-book <name>]

    Resource <name>
      The address book name, string

    Manages:
      addr - SharedAddrBookAddr resources
      set  - SharedAddrBookAddrSet resources
    """
    PROPERTIES = [
        'description',
        '$addrs',         # read-only addresss
        '$sets',          # read-only address-sets
        'zone_list'       # attached zone
    ]

    def __init__(self, junos, name=None, **kvargs):
        if name is None:
            # resource-manager
            Resource.__init__(self, junos, name, **kvargs)
            return

        self.addr = SharedAddrBookAddr(junos, parent=self)
        self.set = SharedAddrBookSet(junos, parent=self)
        self._manages = ['addr', 'set']
        Resource.__init__(self, junos, name, **kvargs)

    def _xml_at_top(self):
        return E.security(
            E('address-book', E.name(self._name))
        )

    # -----------------------------------------------------------------------
    # XML reading
    # -----------------------------------------------------------------------

    def _xml_hook_read_begin(self, xml):
        ab = xml.find('.//address-book')
        ab.append(E('description'))
        ab.append(E('address', JXML.NAMES_ONLY))
        ab.append(E('address-set', JXML.NAMES_ONLY))
        ab.append(E('attach'))
        return True

    def _xml_at_res(self, xml):
        return xml.find('.//address-book')

    def _xml_to_py(self, as_xml, to_py):
        Resource._r_has_xml_status(as_xml, to_py)
        Resource.copyifexists(as_xml, 'description', to_py)
        to_py['$addrs'] = [name.text for name in as_xml.xpath('address/name')]
        to_py['$sets'] = [
            name.text for name in as_xml.xpath('address-set/name')]

    # -----------------------------------------------------------------------
    # XML writing
    # -----------------------------------------------------------------------

    def _xml_change_zone_list(self, xml):
        x_attach = E('attach')
        self._xml_list_property_add_del_names(x_attach,
                                              prop_name='zone_list',
                                              element_name='zone')
        xml.append(x_attach)
        return True

    # -----------------------------------------------------------------------
    # Manager List, Catalog
    # -----------------------------------------------------------------------

    def _r_list(self):
        raise RuntimeError("Need to implement!")

    def _r_catalog(self):
        raise RuntimeError("Need to implement!")
