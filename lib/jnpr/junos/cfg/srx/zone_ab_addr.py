# 3rd-party modules
from lxml.builder import E

# module packages
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML


class ZoneAddrBookAddr(Resource):

    """
    [edit security zone security-zone <zone> address-book address <name>]

    Resource name: str
      <name> is the name of the address item

    Managed by: ZoneAddrBook
      <zone> is the name of the security zone
    """

    PROPERTIES = [
        'description',
        'ip_prefix',
    ]

    def _xml_at_top(self):
        return E.security(E.zones(
            E('security-zone',
              E.name(self.P._name),
              E('address-book', E.address(self._name))
              )
        ))

    # -----------------------------------------------------------------------
    # XML reading
    # -----------------------------------------------------------------------

    def _xml_at_res(self, xml):
        return xml.find('.//address-book/address')

    def _xml_to_py(self, as_xml, to_py):
        Resource._r_has_xml_status(as_xml, to_py)
        Resource.copyifexists(as_xml, 'description', to_py)
        to_py['ip_prefix'] = as_xml.find('ip-prefix').text

    # -----------------------------------------------------------------------
    # XML writing
    # -----------------------------------------------------------------------

    def _xml_change_ip_prefix(self, xml):
        xml.append(E('ip-prefix', self.should['ip_prefix']))
        return True

    # -----------------------------------------------------------------------
    # Manager List, Catalog
    # -----------------------------------------------------------------------

    def _r_list(self):
        #  The parent keeps a property on this list, so just use it, yo!
        self._rlist = self.P['$addrs']

    def _r_catalog(self):
        get = E.security(E.zones(
            E('security-zone',
              E.name(self.P._name),
              E('address-book', E('address'))
              )
        ))
        got = self.D.rpc.get_config(get)
        for addr in got.xpath('.//address-book/address'):
            name = addr.find('name').text
            self._rcatalog[name] = {}
            self._xml_to_py(addr, self._rcatalog[name])
