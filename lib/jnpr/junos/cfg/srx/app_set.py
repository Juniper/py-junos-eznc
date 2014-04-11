# 3rd-party
from lxml.builder import E

# module packages
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML


class ApplicationSet(Resource):

    """
    [edit applications application-set <name>]

    Resource name: str
      <name> is the application-set name
    """

    PROPERTIES = [
        'description',
        'app_list', 'app_list_adds', 'app_list_dels',
        'appset_list', 'appset_list_adds', 'appset_list_dels'
    ]

    def _xml_at_top(self):
        return E.applications(E('application-set', (E.name(self._name))))

    def _xml_at_res(self, xml):
        return xml.find('.//application-set')

    def _xml_to_py(self, has_xml, has_py):
        Resource._r_has_xml_status(has_xml, has_py)
        Resource.copyifexists(has_xml, 'description', has_py)

        # each of the <application> elements
        app_list = [this.findtext('name')
                    for this in has_xml.xpath('application')]
        set_list = [this.findtext('name')
                    for this in has_xml.xpath('application-set')]

        if len(app_list):
            has_py['app_list'] = app_list
        if len(set_list):
            has_py['appset_list'] = set_list

    # -----------------------------------------------------------------------
    # XML property writers
    # -----------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # application list
    # -------------------------------------------------------------------------

    def _xml_change_app_list(self, xml):
        self._xml_list_property_add_del_names(xml,
                                              prop_name='app_list',
                                              element_name='application')
        return True

    def _xml_change_app_list_adds(self, xml):
        for this in self.should['app_list_adds']:
            xml.append(E.application(E.name(this)))
        return True

    def _xml_change_app_list_dels(self, xml):
        for this in self.should['app_list_dels']:
            xml.append(E.application(JXML.DEL, E.name(this)))
        return True

    # -------------------------------------------------------------------------
    # application-set list
    # -------------------------------------------------------------------------

    def _xml_change_appset_list(self, xml):
        if None == self.should.get('appset_list'):
            self['appset_list'] = []

        (adds, dels) = Resource.diff_list(
            self.has.get('appset_list', []), self.should['appset_list'])

        for this in adds:
            xml.append(E('application-set', E.name(this)))
        for this in dels:
            xml.append(E('application-set', JXML.DEL, E.name(this)))
        return True

    def _xml_change_appset_list_adds(self, xml):
        for this in self.should['appset_list_adds']:
            xml.append(E('application-set', E.name(this)))
        return True

    def _xml_change_appset_list_dels(self, xml):
        for this in self.should['appset_list_dels']:
            xml.append(E('application-set', JXML.DEL, E.name(this)))
        return True

    # -----------------------------------------------------------------------
    # Resource List, Catalog
    # -- only executed by 'manager' resources
    # -----------------------------------------------------------------------

    def _r_list(self):
        got = self.R.get_config(
            E.applications(E('application-set', JXML.NAMES_ONLY)))
        self._rlist = [this.text for this in got.xpath('.//name')]

    def _r_catalog(self):
        got = self.R.get_config(E.applications(E('application-set')))
        for this in got.xpath('.//application-set'):
            name = this.findtext('name')
            self._rcatalog[name] = {}
            self._xml_to_py(this, self._rcatalog[name])
