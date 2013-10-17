
import pdb

# stdlib
import os

# 3rd-party packages
import jinja2
from lxml import etree
from lxml.builder import E

# local modules
from .. import TemplateResource
from ..resource import P_JUNOS_ACTIVE, P_JUNOS_EXISTS
from ... import jxml as JXML
from .j2 import _J2LDR

_RD_TEMPLATE = 'nat_src_simple__rd'
_WR_TEMPLATE = 'nat_src_simple__wr'

_XPATH_NAMES = dict(
  pool_name='nat/source/pool',
  ruleset_name='nat/source/rule-set',
  rule_name='nat/source/rule-set/rule'
)

class NatSourceSimple( TemplateResource ):

  PROPERTIES = [
    'zone_from',              # name of from-zone
    'zone_to',                # name of to-zone
    'match_src_addr',         # rule/match source-address
    'match_dst_addr',         # rule/match destination-address
    'pool_from_addr',         # pool/address starting address
    'pool_to_addr',           # pool/address ending address
  ]

  def __init__(self, junos, name=None, **kvargs):
    TemplateResource.__init__(self,junos,name,**kvargs)
    self._xpath_names = _XPATH_NAMES
    self._j2_ldr = _J2LDR
    self._j2_rd = _RD_TEMPLATE
    self._j2_wr = _WR_TEMPLATE

    if self.is_mgr: return

    self._name = self._r_template_names( name )

  def _r_template_names( self, name ):
    if isinstance(name, str):
      # if given a string, then default all the names to the same value
      return dict(ruleset_name=name, pool_name=name, rule_name=name)

    if isinstance(name, dict):
      # otherwise the name is a dictionary of the individual template names
      t_names = dict(name)
      try:
        t_names['pool_name'] = name['pool_name']
        t_names['rule_name'] = name['rule_name']
      except KeyError:
        if not t_names.get('pool_name'): t_names['pool_name'] = name['ruleset_name']
        if not t_names.get('rule_name'): t_names['rule_name'] = name['ruleset_name']
      return t_names      
    else:
      raise RuntimeError("don't know what to do with resource name")

  ##### -----------------------------------------------------------------------
  ##### XML reading
  ##### -----------------------------------------------------------------------

  def _xml_to_py( self, as_xml, to_py ):
    """
      convert the read XML config into python dictionary
    """

    # create a dictionary of names to XML elements

    xml_ele = dict(
      pool_name = as_xml.find('.//source/pool'),
      ruleset_name = as_xml.find('.//source/rule-set'))
    e = as_xml.xpath('.//rule[name=$rule_name]', rule_name=self._name['rule_name'])
    xml_ele['rule_name'] = e[0] if len(e) else None

    # set the exist/active for each
    self._set_ea_status( xml_ele, to_py )

    if xml_ele['pool_name'] is not None:
      e = xml_ele['pool_name']
      to_py['pool_from_addr'] = e.find('address/name').text
      to_py['pool_to_addr'] = e.find('address/to/ipaddr').text

    e = xml_ele['ruleset_name']
    to_py['zone_from'] = e.find('from/zone').text
    to_py['zone_to'] = e.find('to/zone').text

    if xml_ele['rule_name'] is not None:
      e = xml_ele['rule_name']
      to_py['match_src_addr'] = e.find('.//source-address').text
      to_py['match_dst_addr'] = e.find('.//destination-address').text

    return True

  ##### -----------------------------------------------------------------------
  ##### XML writing
  ##### -----------------------------------------------------------------------

  def _xml_set_defaults(self):
    self['match_src_addr'] = self.should.get('match_src_addr', '0.0.0.0/0')
    self['match_dst_addr'] = self.should.get('match_dst_addr', '0.0.0.0/0')

  def _xml_template_write(self):

    # set up templar vars for rending, starting with the
    # resource template names

    t_vars = dict(self._name)

    self._xml_set_defaults()

    if self.should.has_key('pool_from_addr') or self.should.has_key('pool_to_addr'):
      t_vars['_pool_'] = True

    if self.should.has_key('zone_from') or self.should.has_key('zone_to'):
      t_vars['_rule_set_'] = True

    if self.should.has_key('match_src_addr') or self.should.has_key('match_dst_addr'):
      t_vars['_rule_set_'] = True
      t_vars['_rule_'] = True

    t_vars.update( self.has )
    t_vars.update( self.should )

    t = self._j2_ldr.get_template( self._j2_wr+'.j2.xml' ) 
    return etree.XML(t.render( t_vars ))

  ##### -----------------------------------------------------------------------
  ##### XML Junos commands
  ##### -----------------------------------------------------------------------    

  def _xml_template_rename(self, new_name):
    """
      ~! work in progress !~
    """
    # create a tmp dictionary
    _tmp_names = self._r_template_names( new_name )

    # remove the existing configuration
    self._xml_config_write(self._xml_template_delete())

    # change the names
    self._name.update( _tmp_names)

    # return fully created the config
    return self._xml_template_write()



