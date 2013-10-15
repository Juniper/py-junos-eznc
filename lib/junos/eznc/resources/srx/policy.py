import pdb

# 3rd-party modules
from lxml.builder import E 

# module packages
from ..resource import Resource
from .policyrule import PolicyRule

from junos.eznc import jxml as JXML

class PolicyContext( Resource ):
  """
    SRX security policy context
    [edit security policy from-zone <from_zone> to-zone <to_zone>]

    namekey is a tuple( from_zone, to_zone )

    Manages attribute :rule: of type PolicyRule
  """

  PROPERTIES = [
    'rules',
    'rules_count'
  ]

  def __init__(self, junos, name=None, **kvargs ):
    Resource.__init__( self, junos, name, **kvargs )
    if True == self.is_mgr: 
      return

    self.rule = PolicyRule( junos, M=self, parent=self )
    self._name_from_zone = name[0]
    self._name_to_zone = name[1]

  def _xml_at_top(self):
    """
      configuration to retrieve resource
    """
    return E.security( E.policies(
      E.policy(
        E('from-zone-name', self._name_from_zone),
        E('to-zone-name', self._name_to_zone)
      )))

  ### -------------------------------------------------------------------------
  ### XML reading
  ### -------------------------------------------------------------------------

  def _xml_config_read(self):
    """
      ~~~OVERRIDING standard :Resource:
      read the resource config from the Junos device
    """
    xml = self._xml_at_top()
    xml.find('.//policy').append(E.policy(JXML.NAMES_ONLY))
    return self._junos.rpc.get_config( xml )

  def _xml_at_res(self, xml):
    """
      return Element at resource
    """
    return xml.find('.//policy')

  def _xml_to_py(self, as_xml, to_py ):
    """
      converts Junos XML to native Python
    """
    Resource.set_ea_status( as_xml, to_py )
    to_py['rules'] = [policy.text for policy in as_xml.xpath('.//policy/name')]
    to_py['rules_count'] = len(to_py['rules'])

  ##### -----------------------------------------------------------------------
  ##### Resource List, Catalog
  ##### -- only executed by 'manager' resources
  ##### -----------------------------------------------------------------------

  def _r_list(self):
    """
      build the policy context resource list from the command~
      > show security policies zone-context
    """
    got = self._junos.rpc.get_firewall_policies( zone_context=True )
    for pc in got.xpath('//policy-zone-context/policy-zone-context-entry'):
      from_zone = pc.find('policy-zone-context-from-zone').text
      to_zone = pc.find('policy-zone-context-to-zone').text
      self._rlist.append(( from_zone, to_zone ))

  def _r_catalog(self):
    got = self._junos.rpc.get_firewall_policies( zone_context=True )
    for pc in got.xpath('//policy-zone-context/policy-zone-context-entry'):
      from_zone = pc.find('policy-zone-context-from-zone').text
      to_zone = pc.find('policy-zone-context-to-zone').text
      count = int(pc.find('policy-zone-context-policy-count').text)
      self._rcatalog[(from_zone,to_zone)] = {'rules_count': count }
