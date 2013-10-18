
import pdb

# 3rd-party modules
from lxml.builder import E 

# module packages
from ...resource import Resource
from .... import jxml as JXML
from .nat_src_rule import NatSrcRule

class NatSrcRuleSet( Resource ):
  """
  [edit security nat source rule-set <name>]
  """

  PROPERTIES = [
    "zone_from",
    "zone_to"
  ]

  def __init__(self, junos, name=None, **kvargs ):
    Resource.__init__( self, junos, name, **kvargs )
    if True == self.is_mgr: 
      return

    self.rule = NatSrcRule( junos, M=self, parent=self )

  ##### -----------------------------------------------------------------------
  ##### XML read
  ##### -----------------------------------------------------------------------

  def _xml_at_top(self):
    """
      configuration to retrieve resource
    """
    return E.security(E.nat(E.source(
      E('rule-set',
        E.name(self._name),
        E('from'),
        E('to')
      )
    )))

  def _r_config_read_xml(self):
    """
    ~! OVERLOADS !~
      read the resource config from the Junos device
    """
    xml = self._xml_at_top()
    xml.find('.//rule-set').append(E.rule(JXML.NAMES_ONLY))
    cfg_xml = self._junos.rpc.get_config( xml )
    return self._xml_at_res( cfg_xml )

  def _xml_at_res(self, xml):
    """
      return Element at resource
    """
    return xml.find('.//rule-set')

  def _xml_to_py(self, as_xml, to_py ):
    """
      converts Junos XML to native Python
    """
    Resource._r_has_xml_status( as_xml, to_py )
    to_py['zone_from'] = as_xml.find('from/zone').text
    to_py['zone_to'] = as_xml.find('to/zone').text
    to_py['rules'] = [rule.text for rule in as_xml.xpath('.//rule/name')]
    to_py['rules_count'] = len(to_py['rules'])

  ##### -----------------------------------------------------------------------
  ##### XML write
  ##### -----------------------------------------------------------------------

  def _r_config_write_xml(self, xml):
    """
    ~! OVERLOADS !~
    """
    # need to remove the 'stub' <from> and <to> elements
    # that were created from _xml_at_top()

    for stub in [xml.find('from'), xml.find('to')]:
      stub.getparent().remove(stub)

    # now continue with our normally scheduled program ...
    return super(self.__class__,self)._r_config_write_xml(xml)    

  def _xml_change_zone_from( self, xml ):
    xml.append(E('from', JXML.REPLACE, E.zone( self.should['zone_from'])))
    return True

  def _xml_change_zone_to( self, xml ):
    xml.append(E('to', JXML.REPLACE, E.zone( self.should['zone_to'])))
    return True

  ##### -----------------------------------------------------------------------
  ##### Resource List, Catalog
  ##### -- only executed by 'manager' resources
  ##### -----------------------------------------------------------------------

  def _r_list(self):
    get = E.security(E.nat(E.source(
      E('rule-set', JXML.NAMES_ONLY)
    )))
    got = self.J.rpc.get_config( get )
    self._rlist = [name.text for name in got.xpath('.//name')]

  def _r_catalog(self):
    get = E.security(E.nat(E.source(
      E('rule-set')
    )))
    got = self.J.rpc.get_config( get )
    for ruleset in got.xpath('.//rule-set'):
      name = ruleset.find("name").text
      self._rcatalog[name] = {}
      self._xml_to_py( ruleset, self._rcatalog[name] )
    
