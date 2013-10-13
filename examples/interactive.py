import pdb

from exampleutils import *
import junos_eznetconf as junos
from junos_eznetconf import EzNetconf as Junos
from lxml.builder import E 
from lxml import etree

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)

jdev.open()

from junos_eznetconf import EzResource

class SrxApp( EzResource ):

  PROPERTIES = [
    'protocol',
    'destination-port',
    'timeout'
  ]

  def __init__(self, junos, namekey=None, **kvargs ):
    EzResource.__init__( self, junos, namekey, **kvargs )
    self.properties = EzResource.PROPERTIES + self.__class__.PROPERTIES

  def _xml_at_top(self):
    xml = E.applications(
      E.application(
        E.name( self._name )
      )
    )
    return xml

  def _xml_get_has_xml(self, xml):
    return xml.find('.//application')

  def _xml_read_parser(self, has_xml, has_py ):
    self._set_ea_status( has_xml, has_py )

    has_py['protocol'] = has_xml.find('protocol').text
    has_py['destination-port'] = has_xml.find('destination-port').text
    has_py['timeout'] = int(has_xml.find('inactivity-timeout').text)


apps = SrxApp( jdev )



