
# 3rd-party modules
from lxml.builder import E 

# module packages
from ..resource import Resource

class Application( Resource ):
  """
    SRX application resource:
    [edit applications application <name>]
  """

  PROPERTIES = [
    'description',
    'protocol',
    'dest_port',
    'timeout'
  ]

  def __init__(self, junos, name=None, **kvargs ):
    Resource.__init__( self, junos, name, **kvargs )

  def _xml_at_top(self):
    """
      configuration to retrieve resource
    """
    return E.applications(
      E.application(E.name( self._name ))
    )

  def _xml_at_res(self, xml):
    """
      return Element at resource
    """
    return xml.find('.//application')

  def _xml_to_py(self, has_xml, has_py ):
    """
      converts Junos XML to native Python
    """
    self._set_ea_status( has_xml, has_py )

    has_py['protocol'] = has_xml.find('protocol').text
    has_py['dest_port'] = has_xml.find('destination-port').text
    has_py['timeout'] = int(has_xml.find('inactivity-timeout').text)

  ##### -----------------------------------------------------------------------
  ##### XML property writers
  ##### -----------------------------------------------------------------------

  def _xml_change_protocol( self, xml ):
    xml.append(E.protocol(self['protocol']))
    return True

  def _xml_change_dest_port( self, xml ):
    """
      destination-port could be a single value or a range.
      handle the case where the value could be provided as either
      a single int value or a string range, e.g. "1-27"
    """
    value = self['dest_port']
    if isinstance(value,int): value = str(value)
    xml.append(E('destination-port', value))
    return True

  def _xml_change_timeout( self, xml ):
    xml.append(E('inactivity-timeout', str(self['timeout'])))
    return True
