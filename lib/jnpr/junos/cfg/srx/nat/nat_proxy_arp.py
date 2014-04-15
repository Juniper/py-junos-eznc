# 3rd-party modules
from lxml.builder import E

# module packages
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML


class NatProxyArp(Resource):

    """
    [edit security nat proxy-arp interface <if_name> address <ip_prefix>]

    Resource namevar:
      tuple(if_name, ip_prefix)

    Description:
      This resource allows you to add/remove proxy-arp entries for NAT.  At
      this time, there are no managed properties, so you can simply add or
      remove entries by the name tuple(if_name, ip_prefix)

      For example, to select an entry directly:

        entry = NatProxyArp(jdev, ('reth0.213','198.18.11.5'))

      Or using the bind mechanism:

        jdev.bind(parp=NatProxyArp)
        entry = jdev.parp[('reth0.213', '198.18.11.5')]

      To create it, you need to use the 'touch' option when invoking
      write() since there are no properites for proxy-arp entries

        if not entry.exists:
          entry.write(touch=True)

      And to remove the same entry:

        entry.delete()
    """

    def _xml_at_top(self):
        return E.security(E.nat(
            E('proxy-arp',
              E.interface(E.name(self._name[0]),
                          E.address(E.name(self._name[1]))
                          )
              )
        ))

    # -----------------------------------------------------------------------
    # OVERLOADS
    # -----------------------------------------------------------------------

    def rename(self, name):
        """ UNSUPPORTED """
        raise RuntimeError(
            "Unsupported for Resource: %s" %
            self.__class__.__name__)

    # -----------------------------------------------------------------------
    # XML read
    # -----------------------------------------------------------------------

    def _xml_at_res(self, xml):
        return xml.find('.//proxy-arp/interface')

    def _xml_to_py(self, as_xml, to_py):
        Resource._r_has_xml_status(as_xml, to_py)

    # -----------------------------------------------------------------------
    # Resource List, Catalog
    # -- only executed by 'manager' resources
    # -----------------------------------------------------------------------

    def _r_list(self):
        raise RuntimeError("@@@ NEED TO IMPLEMENT!")

    def _r_catalog(self):
        raise RuntimeError("@@@ NEED TO IMPLEMENT!")
