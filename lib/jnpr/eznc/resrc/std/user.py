# 3rd-party modules
from lxml.builder import E 

# module packages
from .. import Resource
from ... import jxml as JXML
from .user_ssh_key import UserSSHKey 

class User( Resource ):
  """
  [edit system login user <name>]

  Resource name: str
    <name> is the user login name

  Manages resources:
    sshkey, UserSSHKey     
  """

  PROPERTIES = [
    'uid',  
    'description',    # the full-name field
    'group',          # user class
    'password',       # write-only clear-text password, will get crypt'd
    '$password',      # read-only crypt'd password
    '$sshkeys',       # names of ssh-keys
  ]

  ##### -----------------------------------------------------------------------
  ##### CONSTRUCTOR
  ##### -----------------------------------------------------------------------

  def __init__(self, junos, name=None, **kvargs ):    
    if name is None: # manager
      Resource.__init__( self, junos, name, **kvargs )
      return

    self.sshkey = UserSSHKey( junos, parent=self )
    self._manages = ['sshkey']
    Resource.__init__( self, junos, name, **kvargs )

  ##### -----------------------------------------------------------------------
  ##### XML readers
  ##### -----------------------------------------------------------------------

  def _xml_at_top(self):
    return E.system(E.login(E.user(E.name(self._name ))))

  def _xml_at_res(self, xml):
    return xml.find('.//user')

  def _xml_to_py(self, has_xml, has_py ):
    Resource._r_has_xml_status( has_xml, has_py )
    has_py['group'] = has_xml.findtext('class')

    Resource.copyifexists( has_xml, 'full-name', has_py, 'description' )
    
    Resource.copyifexists( has_xml, 'uid', has_py )
    if 'uid' in has_py: has_py['uid'] = int(has_py['uid'])

    auth = has_xml.find('authentication')
    if auth is not None:
      # plain-text password
      Resource.copyifexists( auth, 'encrypted-password', has_py, '$password')

      # ssh-keys
      sshkeys = auth.xpath('ssh-rsa | ssh-dsa')
      if sshkeys is not None:
        has_py['$sshkeys'] = [(sshkey.tag, sshkey.findtext('name').strip())
          for sshkey in sshkeys
        ]

  ##### -----------------------------------------------------------------------
  ##### XML property writers
  ##### -----------------------------------------------------------------------

  def _xml_change_description(self, xml):
    xml.append(E('full-name', self['description']))
    return True

  def _xml_change_group(self, xml):
    xml.append(E('class', self['group']))
    return True

  def _xml_change_password(self,xml):
    xml.append(E.authentication(
      E('plain-text-password-value', self['password'])
    ))
    return True

  def _xml_change_uid(self,xml):
    xml.append(E.uid( str(self['uid'] )))
    return True

  ##### -----------------------------------------------------------------------
  ##### Manager List, Catalog
  ##### -----------------------------------------------------------------------

  def _r_list(self):
    get = E.system(E.login(E.user( JXML.NAMES_ONLY )))
    got = self.N.rpc.get_config( get )
    self._rlist = [name.text for name in got.xpath('.//user/name')]

  def _r_catalog(self):
    raise RuntimeError("NEED TO IMPLEMENT!")

    # get = E.applications(E.application())
    # got = self.N.rpc.get_config( get )
    # for app in got.xpath('applications/application'):
    #   name = app.findtext('name')
    #   self._rcatalog[name] = {}
    #   self._xml_to_py( app, self._rcatalog[name] )

