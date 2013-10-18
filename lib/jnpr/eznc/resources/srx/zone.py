# debuggin
import pdb
from lxml import etree

# 3rd-party modules
from lxml.builder import E 

# module packages
from ... import jxml as JXML
from .. import Resource
from .addrbook import ZoneAddrBook
from .zoneifs import ZoneInterface, HostInbSvcMixin

class Zone( HostInbSvcMixin, Resource ):
  """
  [edit security zone security-zone <zone>]

  Manages:
    :ifs:     ZoneInterface
    :ab:      ZoneAddressBook
  """
  PROPERTIES = [
    'description',
    'services',
    'protocols',
    '$ifs_list'
  ]
  def __init__(self, junos, name=None, **kvargs ):
    Resource.__init__( self, junos, name, **kvargs )

    if True == self.is_mgr: return

    self.ifs = ZoneInterface( junos, parent=self )
    self.ab = ZoneAddrBook( junos, name, parent=self )
    self._manages = ['ifs','ab']

  ##### -----------------------------------------------------------------------
  ##### XML reading
  ##### -----------------------------------------------------------------------

  def _xml_at_top(self):
    return E.security(E.zones(
      E('security-zone',E.name( self._name ))
    ))

  def _xml_hook_read_begin(self, xml):
    e = xml.find('.//security-zone')
    e.append(E('host-inbound-traffic'))
    e.append(E('description'))
    e.append(E('interfaces'))
    return True

  def _xml_at_res(self, xml):
    return xml.find('.//security-zone')

  def _xml_to_py(self, as_xml, to_py ):
    Resource._r_has_xml_status( as_xml, to_py )
    Resource.copyifexists( as_xml, 'description', to_py)

    e = as_xml.xpath('host-inbound-traffic/system-services/name')
    to_py['services'] = [n.text for n in e]
    e = as_xml.xpath('host-inbound-traffic/protocols/name')
    to_py['protocols'] = [n.text for n in e]

    to_py['$ifs_list'] = [name.text for name in as_xml.xpath('interfaces/name')]
  
  ##### -----------------------------------------------------------------------
  ##### XML writing
  ##### -----------------------------------------------------------------------

  # handled by mixin

  ##### -----------------------------------------------------------------------
  ##### Manager List, Catalog
  ##### -----------------------------------------------------------------------

  def _r_list(self):
    """
    list of security zones
    """
    got = self.J.rpc.get_zones_information(terse=True)
    zones = got.findall('zones-security/zones-security-zonename')
    self._rlist = [zone.text for zone in zones]

  def _r_catalog(self):
    """
    """
    raise RuntimeError("Need to implement!")
