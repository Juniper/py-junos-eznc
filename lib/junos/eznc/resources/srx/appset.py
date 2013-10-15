
import pdb

# 3rd-party
from lxml.builder import E 

# module packages
from ..resource import Resource
from junos.eznc import jxml as JNX

class ApplicationSet( Resource ):
  """
    SRX application resource:
    [edit applications application-set <name>]
  """

  PROPERTIES = [
    'description',
    'app_list',     'app_list_adds',    'app_list_dels',
    'appset_list',  'appset_list_adds', 'appset_list_dels'
  ]

  def __init__(self, junos, name=None, **kvargs ):
    Resource.__init__( self, junos, name, **kvargs )

  def _xml_at_top(self):
    """
      configuration to retrieve resource
    """
    return E.applications(E('application-set', (E.name( self._name ))))

  def _xml_at_res(self, xml):
    """
      return Element at resource
    """
    return xml.find('.//application-set')

  def _xml_to_py(self, has_xml, has_py ):
    """
      converts Junos XML to native Python
    """
    Resource.set_ea_status( has_xml, has_py )

    has_py['app_list'] = []
    has_py['appset_list'] = []

    Resource.copyifexists( has_xml, 'description', has_py )

    # each of the <application> elements
    for this in has_xml.xpath('application'):
      has_py['app_list'].append(this.find('name').text)

    # sets can contain other sets too ...
    for this in has_xml.xpath('application-set'):
      has_py['appset_list'].append(this.find('name').text)

  ##### -----------------------------------------------------------------------
  ##### XML property writers
  ##### -----------------------------------------------------------------------

  ### -------------------------------------------------------------------------
  ### application list
  ### -------------------------------------------------------------------------

  def _xml_change_app_list( self, xml ):
    if None == self.should.get('app_list'): self['app_list'] = []

    (adds,dels) = Resource.diff_list( self.has.get('app_list',[]), self.should['app_list'])

    for this in adds: xml.append(E.application(E.name(this)))
    for this in dels: xml.append(E.application(JNX.DEL, E.name(this)))
    return True

  def _xml_change_app_list_adds( self, xml ):
    for this in self.should['app_list_adds']:
      xml.append(E.application(E.name(this)))
    return True

  def _xml_change_app_list_dels( self, xml ):
    for this in self.should['app_list_dels']:
      xml.append(E.application(JNX.DEL, E.name(this)))
    return True

  ### -------------------------------------------------------------------------
  ### application-set list
  ### -------------------------------------------------------------------------

  def _xml_change_appset_list( self, xml ):
    if None == self.should.get('appset_list'): self['appset_list'] = []

    (adds,dels) = Resource.diff_list( self.has.get('appset_list',[]), self.should['appset_list'])

    for this in adds: xml.append(E('application-set',E.name(this)))
    for this in dels: xml.append(E('application-set', JNX.DEL, E.name(this)))
    return True

  def _xml_change_appset_list_adds( self, xml ):
    for this in self.should['appset_list_adds']:
      xml.append(E('application-set',E.name(this)))
    return True    

  def _xml_change_appset_list_dels( self, xml ):
    for this in self.should['appset_list_dels']:
      xml.append(E('application-set', JNX.DEL, E.name(this)))
    return True    

  ##### -----------------------------------------------------------------------
  ##### Resource List, Catalog
  ##### -- only executed by 'manager' resources
  ##### -----------------------------------------------------------------------

  def _r_list(self):

    got = self._junos.rpc.get_config(
      E.applications(E('application-set', JNX.NAMES_ONLY)))

    self._rlist = [ this.text for this in got.xpath('.//name')]

  def _r_catalog(self):

    got = self._junos.rpc.get_config(
      E.applications(E('application-set')))

    for this in got.xpath('.//application-set'):
      name = this.find('name').text
      this_py = {}
      self._xml_to_py( this, this_py )
      self._rcatalog[name] = this_py



