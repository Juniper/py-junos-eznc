
import pdb

# 3rd-party modules
from lxml.builder import E 

# module packages
from ...resource import Resource
from .... import jxml as JXML
from .nat_proxy_arp import NatProxyArp

class NatStaticRule( Resource ):
  """
  [edit security nat static rule-set <ruleset-name> rule <rule-name>]
  """

  PROPERTIES = [
   "description",
   "match_dst_addr",
   "match_dst_port",
   "nat_addr",
   "nat_port",
   "proxy_interface"
  ]

  ##### -----------------------------------------------------------------------
  ##### XML read
  ##### -----------------------------------------------------------------------

  def _xml_at_top(self):
    return E.security(E.nat(E.static(
      E('rule-set',
        E.name(self.P._name),
        E.rule(E.name(self._name))
      )
    )))

  def _xml_at_res(self, xml):
    return xml.find('.//rule')

  def _xml_to_py(self, as_xml, to_py ):
    """
    converts Junos XML to native Python
    """
    Resource._r_has_xml_status( as_xml, to_py )
    Resource.copyifexists( as_xml, 'description', to_py)    
    e = as_xml.find('static-nat-rule-match')
    to_py['match_dst_addr'] = e.find('destination-address').text

  ##### -----------------------------------------------------------------------
  ##### XML write
  ##### -----------------------------------------------------------------------

  def _xml_hook_build_change_begin( self, xml ):
    if 'nat_port' not in self.should:
      self.should['nat_port'] = self['match_dst_port']

    if 'match_dst_addr' in self.should and 'proxy_interface' in self.has:
      if 'proxy_interface' not in self.should:
        # force a flush on the proxy-interface.  this is really a hack
        # @@@ need to fix this correctly
        self.should['proxy_interface'] = self.has['proxy_interface']

    match = E('static-nat-rule-match')
    xml.append(match)
    then = E.then(E('static-nat', E('prefix')))
    xml.append(then)
    self._rxml_match = match
    self._rxml_then = then.find('static-nat/prefix')

  def _xml_change_match_dst_addr(self, xml):
    self._rxml_match.append(
      E('destination-address', JXML.REPLACE, self.should['match_dst_addr'])
    )
    return True

  def _xml_change_match_dst_port(self,xml):
    self._rxml_match.append(
      E('destination-port', E.low(self.should['match_dst_port']))
    )
    return True

  def _xml_change_nat_addr(self, xml):
    self._rxml_then.append(E('addr-prefix', self.should['nat_addr']))
    return True

  def _xml_change_nat_port(self, xml):
    self._rxml_then.append(E('mapped-port', E('low', self.should['nat_port'])))
    return True

  def _xml_change_proxy_interface(self, xml):
    proxy_arp = NatProxyArp(self._junos, self.should['proxy_interface'], P=self)
    proxy_arp['ip_prefix'] = self['match_dst_addr']
    proxy_arp.write()
    return True

  ##### -----------------------------------------------------------------------
  ##### Manager List, Catalog
  ##### -----------------------------------------------------------------------

  def _r_list(self):
    self._rlist = self.P['rules']

  def _r_catalog(self):
    get = E.security(E.nat(E.static(
      E('rule-set',
        E.name(self.P._name),
      )
    )))
    got = self.J.rpc.get_config( get )
    for rule in got.xpath('.//rule'):
      name = rule.find('name').text
      self._rcatalog[name] = {}
      self._xml_to_py( rule, self._rcatalog[name] )