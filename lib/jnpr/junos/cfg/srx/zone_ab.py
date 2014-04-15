# debuggin
from lxml import etree

# 3rd-party modules
from lxml.builder import E

# module packages
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML
from jnpr.junos.cfg.srx.zone_ab_addr import ZoneAddrBookAddr
from jnpr.junos.cfg.srx.zone_ab_set import ZoneAddrBookSet


class ZoneAddrBook(Resource):

    """
    [edit security zone security-zone <zone> address-book]

    Resource name: str
      The zone name

    Resource manages:
      addr, ZoneAddrBookAddr
      set, ZoneAddrBookSet
    """

    PROPERTIES = [
        '$addrs',         # read-only addresss
        '$sets'           # read-only address-sets
    ]

    def __init__(self, junos, name=None, **kvargs):
        if name is None:
            # resource-manager
            Resource.__init__(self, junos, name, **kvargs)
            return

        self.addr = ZoneAddrBookAddr(junos, parent=self)
        self.set = ZoneAddrBookSet(junos, parent=self)
        self._manages = ['addr', 'set']
        Resource.__init__(self, junos, name, **kvargs)

    def _xml_at_top(self):
        return E.security(E.zones(
            E('security-zone',
              E.name(self._name),
              E('address-book',
                E('address', JXML.NAMES_ONLY),
                E('address-set', JXML.NAMES_ONLY)
                )
              )
        ))

    # -----------------------------------------------------------------------
    # XML reading
    # -----------------------------------------------------------------------

    def _xml_at_res(self, xml):
        return xml.find('.//address-book')

    def _xml_to_py(self, as_xml, to_py):
        Resource._r_has_xml_status(as_xml, to_py)
        to_py['$addrs'] = [name.text for name in as_xml.xpath('address/name')]
        to_py['$sets'] = [
            name.text for name in as_xml.xpath('address-set/name')]

    # -----------------------------------------------------------------------
    # Manager List, Catalog
    # -----------------------------------------------------------------------

    def _r_list(self):
        # this list of zone addressbooks is really just the list of zones
        got = self.R.get_zones_information(terse=True)
        zones = got.findall('zones-security/zones-security-zonename')
        self._rlist = [zone.text for zone in zones]
        self._rlist.remove('junos-host')

    # using Resource._r_catalog()
