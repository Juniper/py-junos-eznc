# 3rd-party modules
from lxml.builder import E

# module packages
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML
from jnpr.junos.cfg.user_ssh_key import UserSSHKey


class User(Resource):

    """
    [edit system login user <name>]

    Resource name: str
      <name> is the user login name

    Manages resources:
      sshkey, UserSSHKey
    """

    PROPERTIES = [
        'uid',
        'fullname',       # the full-name field
        'userclass',      # user class
        'password',       # write-only clear-text password, will get crypt'd
        '$password',      # read-only crypt'd password
        '$sshkeys',       # read-only names of ssh-keys
    ]

    MANAGES = {'sshkey': UserSSHKey}

    # -----------------------------------------------------------------------
    # XML readers
    # -----------------------------------------------------------------------

    def _xml_at_top(self):
        return E.system(E.login(E.user(E.name(self._name))))

    def _xml_at_res(self, xml):
        return xml.find('.//user')

    def _xml_to_py(self, has_xml, has_py):
        Resource._r_has_xml_status(has_xml, has_py)

        has_py['userclass'] = has_xml.findtext('class')

        Resource.copyifexists(has_xml, 'full-name', has_py, 'fullname')

        Resource.copyifexists(has_xml, 'uid', has_py)
        if 'uid' in has_py:
            has_py['uid'] = int(has_py['uid'])

        auth = has_xml.find('authentication')
        if auth is not None:
            # plain-text password
            Resource.copyifexists(
                auth,
                'encrypted-password',
                has_py,
                '$password')

            # ssh-keys
            sshkeys = auth.xpath('ssh-rsa | ssh-dsa')
            if sshkeys is not None:
                has_py['$sshkeys'] = [(sshkey.tag,
                                       sshkey.findtext('name').strip())
                                      for sshkey in sshkeys
                                      ]

    # -----------------------------------------------------------------------
    # XML property writers
    # -----------------------------------------------------------------------

    def _xml_change_fullname(self, xml):
        xml.append(E('full-name', self['fullname']))
        return True

    def _xml_change_userclass(self, xml):
        xml.append(E('class', self['userclass']))
        return True

    def _xml_change_password(self, xml):
        xml.append(E.authentication(
            E('plain-text-password-value', self['password'])
        ))
        return True

    def _xml_change_uid(self, xml):
        xml.append(E.uid(str(self['uid'])))
        return True

    # -----------------------------------------------------------------------
    # Manager List, Catalog
    # -----------------------------------------------------------------------

    def _r_list(self):
        get = E.system(E.login(E.user(JXML.NAMES_ONLY)))
        got = self.R.get_config(get)
        self._rlist = [name.text for name in got.xpath('.//user/name')]
