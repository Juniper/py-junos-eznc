
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

_J2LDR = jinja2.Environment(
  trim_blocks=True,
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

_RD_TEMPLATE = 'nat_simple_source__rd.j2.xml'
_WR_TEMPLATE = 'nat_simple_source__wr.j2.xml'

_XPATH_NAMES = dict(
  pool_name='nat/source/pool',
  ruleset_name='nat/source/rule-set',
  rule_name='nat/source/rule-set/rule'
)

class NatSimpleSource( TemplateResource ):

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
    if self.is_mgr: return

    self._template_names = self._r_template_names( name )

  def _r_template_names( self, name ):
    if isinstance(name, str):
      return dict(ruleset_name=name, pool_name=name, rule_name=name)

    if isinstance(name, dict):
      # the caller is passing up the name in a tuple that could be
      # (ruleset_name, *pool_name, *rule_name)
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

  def _xml_template_read(self):
    t = _J2LDR.get_template( _RD_TEMPLATE )    
    return etree.XML(t.render(self._template_names))

  def _xml_to_py( self, as_xml, to_py ):
    x_pool = as_xml.find('.//source/pool')
    x_ruleset = as_xml.find('.//source/rule-set')
    x_rule = x_ruleset.xpath('./rule[name=$rule_name]', rule_name=self._template_names['rule_name'])[0]

    to_py['zone_from'] = x_ruleset.find('from/zone').text
    to_py['zone_to'] = x_ruleset.find('to/zone').text
    to_py['match_src_addr'] = x_rule.find('.//source-address').text
    to_py['match_dst_addr'] = x_rule.find('.//destination-address').text
    to_py['pool_from_addr'] = x_pool.find('address/name').text
    to_py['pool_to_addr'] = x_pool.find('address/to/ipaddr').text

    to_py[P_JUNOS_ACTIVE] = True
    to_py[P_JUNOS_EXISTS] = True

    return True

  ##### -----------------------------------------------------------------------
  ##### XML writing
  ##### -----------------------------------------------------------------------

  def _xml_template_write(self):
    t = _J2LDR.get_template( _WR_TEMPLATE )    

    t_vars = dict(self._template_names)

    if self.should.has_key('pool_from_addr') or self.should.has_key('pool_to_addr'):
      t_vars['_pool_'] = True

    if self.should.has_key('zone_from') or self.should.has_key('zone_to'):
      t_vars['_rule_set_'] = True

    if self.should.has_key('match_src_addr') or self.should.has_key('match_dst_addr'):
      t_vars['_rule_set_'] = True
      t_vars['_rule_'] = True

    t_vars.update( self.has )
    t_vars.update( self.should )

    return etree.XML(t.render( t_vars ))

  ##### -----------------------------------------------------------------------
  ##### XML Junos commands
  ##### -----------------------------------------------------------------------    

  def _xml_template_names_only( self ):
    t = _J2LDR.get_template(_RD_TEMPLATE)
    return etree.XML(t.render(self._template_names, NAMES_ONLY=True))

  def _xml_template_rename(self, new_name):
    
    # create a tmp dictionary
    _tmp_names = self._r_template_names( new_name )

    # remove the existing configuration
    self._xml_config_write(self._xml_template_delete())

    # change the names
    self._template_names.update( _tmp_names)

    # return fully created the config
    return self._xml_template_write()



