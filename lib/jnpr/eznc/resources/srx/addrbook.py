# debuggin
import pdb
from lxml import etree

# 3rd-party modules
from lxml.builder import E 

# module packages
from ... import jxml as JXML
from .. import Resource
from .addrbook_addr import ZoneAddrBookAddr
from .addrbook_set import ZoneAddrBookSet

class ZoneAddrBook( Resource ):
  """
    [edit security zone security-zone <zone> address-book]

    Resource manages two sub-resources:
    .addr - specific address entries
    .set - specific address sets
  """
  PROPERTIES = [
    '$addrs',         # read-only addresss
    '$sets'           # read-only address-sets
  ]
  def __init__(self, junos, name=None, **kvargs ):
    if name is None:
      # resource-manager
      Resource.__init__( self, junos, name, **kvargs )
      return

    self.addr = ZoneAddrBookAddr( junos, parent=self )
    self.set = ZoneAddrBookSet( junos, parent=self )
    self._manages = ['addr','set']
    Resource.__init__( self, junos, name, **kvargs )

  def _xml_at_top(self):
    return E.security(E.zones(
      E('security-zone', 
        E.name( self._name ),
        E('address-book',
          E('address', JXML.NAMES_ONLY),
          E('address-set', JXML.NAMES_ONLY)
        )
      )
    ))

  ##### -----------------------------------------------------------------------
  ##### XML reading
  ##### -----------------------------------------------------------------------
  
  def _xml_at_res(self, xml):
    return xml.find('.//address-book')

  def _xml_to_py(self, as_xml, to_py ):
    Resource._r_has_xml_status( as_xml, to_py )
    to_py['$addrs'] = [name.text for name in as_xml.xpath('address/name')]
    to_py['$sets'] = [name.text for name in as_xml.xpath('address-set/name')]

  ##### -----------------------------------------------------------------------
  ##### Manager List, Catalog
  ##### -----------------------------------------------------------------------

  def _r_list(self):
    """
    """
    raise RuntimeError("Need to implement!")

  def _r_catalog(self):
    """
    """
    raise RuntimeError("Need to implement!")
