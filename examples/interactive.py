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
    'dest_port',
    'timeout'
  ]

  def __init__(self, junos, namekey=None, **kvargs ):
    EzResource.__init__( self, junos, namekey, **kvargs )

  def _xml_at_top(self):
    xml = E.applications(
      E.application(
        E.name( self._name )
      )
    )
    return xml

  def _xml_at_res(self, xml):
    return xml.find('.//application')

  def _xml_read_to_py(self, has_xml, has_py ):
    self._set_ea_status( has_xml, has_py )

    has_py['protocol'] = has_xml.find('protocol').text
    has_py['dest_port'] = has_xml.find('destination-port').text
    has_py['timeout'] = int(has_xml.find('inactivity-timeout').text)

  ##### -----------------------------------------------------------------------
  ##### XML property writers
  ##### -----------------------------------------------------------------------

  def _xml_change_protocol( self, xml ):
    xml.append(E.protocol(self.should['protocol']))
    return True

  def _xml_change_dest_port( self, xml ):
    return False

  def _xml_change_timeout( self, xml ):
    return False

apps = SrxApp( jdev )



