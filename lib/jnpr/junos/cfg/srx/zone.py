# debuggin
from lxml import etree

# 3rd-party modules
from lxml.builder import E

# module packages
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML
from jnpr.junos.cfg.srx.zone_ab import ZoneAddrBook
from jnpr.junos.cfg.srx.zone_ifs import ZoneInterface, HostInbSvcMixin


class Zone(HostInbSvcMixin, Resource):

    """
    [edit security zone security-zone <zone>]

    Resource Name: str
      The zone name

    Manages resources:
      ifs, ZoneInterface
      ab, ZoneAddressBook
    """

    PROPERTIES = [
        'description',
        'services',
        'protocols',
        '$ifs_list'
    ]

    def __init__(self, junos, name=None, **kvargs):
        if name is None:
            # resource-manager
            Resource.__init__(self, junos, name, **kvargs)
            return

        self.ifs = ZoneInterface(junos, parent=self)
        self.ab = ZoneAddrBook(junos, name, parent=self)
        self._manages = ['ifs', 'ab']
        Resource.__init__(self, junos, name, **kvargs)

    # -----------------------------------------------------------------------
    # XML reading
    # -----------------------------------------------------------------------

    def _xml_at_top(self):
        return E.security(E.zones(
            E('security-zone', E.name(self._name))
        ))

    def _xml_hook_read_begin(self, xml):
        e = xml.find('.//security-zone')
        e.append(E('host-inbound-traffic'))
        e.append(E('description'))
        e.append(E('interfaces'))
        return True

    def _xml_at_res(self, xml):
        return xml.find('.//security-zone')

    def _xml_to_py(self, as_xml, to_py):
        Resource._r_has_xml_status(as_xml, to_py)
        Resource.copyifexists(as_xml, 'description', to_py)
        e = as_xml.xpath('host-inbound-traffic/system-services/name')
        to_py['services'] = [n.text for n in e]
        e = as_xml.xpath('host-inbound-traffic/protocols/name')
        to_py['protocols'] = [n.text for n in e]
        to_py['$ifs_list'] = [
            name.text for name in as_xml.xpath('interfaces/name')]

    # -----------------------------------------------------------------------
    # XML writing
    # -----------------------------------------------------------------------

    # handled by mixin, yo!

    # -----------------------------------------------------------------------
    # Manager List, Catalog
    # -----------------------------------------------------------------------

    def _r_list(self):
        got = self.R.get_zones_information(terse=True)
        zones = got.findall('zones-security/zones-security-zonename')
        self._rlist = [zone.text for zone in zones]
        self._rlist.remove('junos-host')

    # using Resource._r_catalog()
