# 3rd-party modules
from lxml.builder import E

# module packages
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML


class NatSrcPool(Resource):

    """
    [edit security nat source pool <name>]
    """

    PROPERTIES = [
        'addr_from',
        'addr_to'
    ]

    def _xml_at_top(self):
        """
        configuration to retrieve resource
        """
        return E.security(E.nat(E.source(E.pool(E.name(self.name)))))

    # -----------------------------------------------------------------------
    # XML read
    # -----------------------------------------------------------------------

    def _xml_at_res(self, xml):
        """
        return Element at resource
        """
        return xml.find('.//pool')

    def _xml_to_py(self, as_xml, to_py):
        """
        converts Junos XML to native Python
        """
        Resource._r_has_xml_status(as_xml, to_py)
        to_py['addr_from'] = as_xml.find('address/name').text
        to_py['addr_to'] = as_xml.find('address/to/ipaddr').text

    # -----------------------------------------------------------------------
    # XML property writers
    # -----------------------------------------------------------------------

    def _xml_change_addr_from(self, xml):
        # we need to always set the address/name given the structure of the
        # Junos configuration XML, derp.

        addr_from = self.should.get('addr_from') or self.has.get('addr_from')
        xml.append(E.address(JXML.REPLACE, E.name(addr_from)))
        return True

    def _xml_change_addr_to(self, xml):
        # we must always include the addr_from, so if we didn't expliclity
        # change it, we must do it now.

        if 'addr_from' not in self.should:
            self._xml_change_addr_from(xml)

        x_addr = xml.find('address')
        x_addr.append(E.to(E.ipaddr(self.should['addr_to'])))
        return True

    # -----------------------------------------------------------------------
    # Resource List, Catalog
    # -- only executed by 'manager' resources
    # -----------------------------------------------------------------------

    def _r_list(self):
        """
          build the policy context resource list from the command~
          > show security policies zone-context
        """
        get = E.security(E.nat(E.source(
            E.pool(JXML.NAMES_ONLY))))

        got = self.D.rpc.get_config(get)
        self._rlist = [name.text for name in got.xpath('.//pool/name')]

    def _r_catalog(self):
        get = E.security(E.nat(E.source(E.pool)))
        got = self.D.rpc.get_config(get)
        for pool in got.xpath('.//pool'):
            name = pool.find('name').text
            self._rcatalog[name] = {}
            self._xml_to_py(pool, self._rcatalog[name])
