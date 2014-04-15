# debuggin
from lxml import etree

# 3rd-party modules
from lxml.builder import E

# module packages
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML


class HostInbSvcMixin(object):

    def _xml_hook_build_change_begin(self, xml):
        """
        HostInbSvcMixin
        """
        def _default_empty(prop_name):
            if prop_name in self.should and self.should[prop_name] is None:
                self.should[prop_name] = []

        _default_empty('services')
        _default_empty('protocols')

    def _xml__change__hit(self, xml, prop, ele_name):
        (adds, dels) = Resource.diff_list(self.has[prop], self.should[prop])
        if not adds and not dels:
            return False

        hit = E('host-inbound-traffic')
        for this in adds:
            hit.append(E(ele_name, E.name(this)))
        for this in dels:
            hit.append(E(ele_name, JXML.DEL, E.name(this)))
        xml.append(hit)
        return True

    def _xml_change_services(self, xml):
        return self._xml__change__hit(xml, 'services', 'system-services')

    def _xml_change_protocols(self, xml):
        return self._xml__change__hit(xml, 'protocols', 'protocols')


class ZoneInterface(HostInbSvcMixin, Resource):

    """
    [edit security zone security-zone <zone> interfaces <name>]

    Resource name: str
      <name> is the interface name, e.g. 'ge-0/0/0.12'

    Managed by: Zone
      <zone> is the name of the security zone
    """

    PROPERTIES = [
        'services',
        'protocols',
    ]

    def _xml_at_top(self):
        return E.security(E.zones(
            E('security-zone',
              E.name(self.P._name),
              E.interfaces(E.name(self._name))
              )
        ))

    # -----------------------------------------------------------------------
    # XML reading
    # -----------------------------------------------------------------------

    def _xml_at_res(self, xml):
        return xml.find('.//interfaces')

    def _xml_to_py(self, as_xml, to_py):
        Resource._r_has_xml_status(as_xml, to_py)
        e = as_xml.xpath('host-inbound-traffic/system-services/name')
        to_py['services'] = [n.text for n in e]
        e = as_xml.xpath('host-inbound-traffic/protocols/name')
        to_py['protocols'] = [n.text for n in e]

    # -----------------------------------------------------------------------
    # XML writing
    # -----------------------------------------------------------------------

    # handled by the mixin

    # -----------------------------------------------------------------------
    # Manager List, Catalog
    # -----------------------------------------------------------------------

    def _r_list(self):
        self._rlist = self.P['$ifs_list']

    # using Resource._r_catalog()
