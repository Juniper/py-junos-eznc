
# 3rd-party modules
from lxml.builder import E 

# module packages
from ...resource import Resource
from .... import jxml as JXML

class NatProxyArp( Resource ):
  """
  [edit security nat proxy-arp interface <name>]
  """

  PROPERTIES = [
    'ip_prefix'
  ]

  def _xml_at_top(self):
    return E.security(E.nat(E('proxy-arp',E.interface(E.name( self._name )))))

  ##### -----------------------------------------------------------------------
  ##### XML read
  ##### -----------------------------------------------------------------------

  def _xml_at_res(self, xml):
    return xml.find('.//proxy-arp/interface')

  def _xml_to_py(self, as_xml, to_py ):
    """
      converts Junos XML to native Python
    """
    Resource._r_has_xml_status( as_xml, to_py )
    to_py['ip_prefix'] = as_xml.find('address/name').text

  ##### -----------------------------------------------------------------------
  ##### XML property writers
  ##### -----------------------------------------------------------------------


  def _xml_change_ip_prefix(self, xml):
    xml.append(E('address', JXML.REPLACE, E.name( self.should['ip_prefix'])))
    return True

  ##### -----------------------------------------------------------------------
  ##### Resource List, Catalog
  ##### -- only executed by 'manager' resources
  ##### -----------------------------------------------------------------------

  def _r_list(self):
    raise RuntimeError("@@@ NEED TO IMPLEMENT!")

  def _r_catalog(self):
    raise RuntimeError("@@@ NEED TO IMPLEMENT!")
