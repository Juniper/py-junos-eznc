# local modules
from .. import TemplateResource
from ..resource import P_JUNOS_ACTIVE, P_JUNOS_EXISTS
from ... import jxml as JXML
from .j2 import _J2LDR

# template files located in the ./templates directory

_RD_TEMPLATE = 'nat_src_simple__rd.j2.xml'
_WR_TEMPLATE = 'nat_src_simple__wr.j2.xml'

# dictionary of resource name items and associated XPath

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

    self._name = self._r_xpath_names( name )

  def _r_xpath_names( self, name ):
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

    xml_ele = {}
    xml_ele['pool_name'] = as_xml.find('.//source/pool')
    xml_ele['ruleset_name']= as_xml.find('.//source/rule-set')
    e = as_xml.xpath('.//rule[name=$rule_name]', rule_name=self._name['rule_name'])
    xml_ele['rule_name'] = e[0] if len(e) else None

    # set the exist/active status for each name
    self._r_has_xml_status( xml_ele, to_py )

    e = xml_ele['ruleset_name']
    to_py['zone_from'] = e.find('from/zone').text
    to_py['zone_to'] = e.find('to/zone').text

    if xml_ele['pool_name'] is not None:
      e = xml_ele['pool_name']
      to_py['pool_from_addr'] = e.find('address/name').text
      to_py['pool_to_addr'] = e.find('address/to/ipaddr').text

    if xml_ele['rule_name'] is not None:
      e = xml_ele['rule_name']
      to_py['match_src_addr'] = e.find('.//source-address').text
      to_py['match_dst_addr'] = e.find('.//destination-address').text

    return True

  ##### -----------------------------------------------------------------------
  ##### XML writing
  ##### -----------------------------------------------------------------------

  def _r_should_defaults(self, t_vars):
    """
      when doing a write, assign default values if they are not present
    """
    def _default_to(p_name,d_val):
      if not t_vars.has_key(p_name): t_vars[p_name] = d_val

    _default_to( 'match_dst_addr', '0.0.0.0/0')
    _default_to( 'match_src_addr', '0.0.0.0/0')

  def _r_template_write_vars(self):
    """
      create a dictionary of variables that will be used to
      render the write-XML configuration
    """

    # set up template vars for rending, starting with the
    # resource names

    t_vars = dict(self._name)

    # then load the :has:, followed by :should:, and then defaults

    t_vars.update( self.has )
    t_vars.update( self.should )
    self._r_should_defaults( t_vars )

    # mark the vars to indicate sections of the XML template to buildup;
    # these markers are specific to the actual template (see file for details)

    if self.should.has_key('pool_from_addr') or self.should.has_key('pool_to_addr'):
      t_vars['_pool_'] = True

    if self.should.has_key('zone_from') or self.should.has_key('zone_to'):
      t_vars['_rule_set_'] = True

    if self.should.has_key('match_src_addr') or self.should.has_key('match_dst_addr'):
      t_vars['_rule_set_'] = True
      t_vars['_rule_'] = True

    return t_vars
