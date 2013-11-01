# local modules
from .. import TemplateResource
from ..resource import P_JUNOS_ACTIVE, P_JUNOS_EXISTS
from ... import jxml as JXML
from .j2 import _J2LDR

# template files located in the ./templates directory

_RD_TEMPLATE = 'nat_static_simple__rd.j2.xml'
_WR_TEMPLATE = 'nat_static_simple__wr.j2.xml'

# dictionary of resource name items and associated XPath

_XPATH_NAMES = dict(
  ruleset_name='nat/static/rule-set',
  rule_name='nat/static/rule-set/rule'
)

class NatStaticSimple( TemplateResource ):

  PROPERTIES = [
    'zone_from',        
    'dst_ip_addr',      
    'dst_port',         
    'src_ip_addr',      
    'src_port',
    'port'                # if set, will be used for [dst_port,src_port]
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
      return dict(ruleset_name=name, rule_name=name)

    if isinstance(name, dict):
      # otherwise the name is a dictionary of the individual template names
      t_names = dict(name)
      try:
        t_names['rule_name'] = name['rule_name']
      except KeyError:
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
    xml_ele['ruleset_name']= as_xml.find('.//static/rule-set')
    e = as_xml.xpath('.//rule[name=$rule_name]', rule_name=self._name['rule_name'])
    xml_ele['rule_name'] = e[0] if len(e) else None

    # set the exist/active status for each name
    self._r_has_xml_status( xml_ele, to_py )

    e = xml_ele['ruleset_name']
    to_py['zone_from'] = e.find('from/zone').text

    if xml_ele['rule_name'] is not None:
      e = xml_ele['rule_name']
      to_py['dst_ip_addr'] = e.find('.//destination-address/dst-addr').text
      to_py['dst_port'] = e.find('.//destination-port/low').text
      e = e.find('.//static-nat/prefix')
      to_py['src_ip_addr'] = e.find('addr-prefix').text
      to_py['src_port'] = e.find('mapped-port/low').text

    return True

  ##### -----------------------------------------------------------------------
  ##### XML writing
  ##### -----------------------------------------------------------------------    

  def _r_template_write_vars(self):
    """
    ~| OVERLOADS |~
    """
    if self.should.has_key('port'):
      # override the values in dst_port and src_port
      port = self['port']
      self['dst_port'] = port
      self['src_port'] = port

    return super(self.__class__,self)._r_template_write_vars()    
