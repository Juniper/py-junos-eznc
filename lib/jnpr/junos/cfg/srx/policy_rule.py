# 3rd-party packages
from lxml.builder import E

# local packages
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML


class PolicyRule(Resource):

    """
    [edit security policy from-zone <from_zone> to-zone <to_zone> policy
        <policy_name>]

    Resource name: str
      <policy_name> is the name of the policy

    Managed by: PolicyContext
      <from_zone> and <to_zone> taken from parent resource
    """

    PROPERTIES = [
        'description',
        'match_srcs',
        'match_dsts',
        'match_apps',
        'action',
        'count',
        'log_init',
        'log_close'
    ]

    # -------------------------------------------------------------------------
    # XML reading
    # -------------------------------------------------------------------------

    def _xml_at_top(self):
        xml = self._parent._xml_at_top()
        xml.find('.//policy').append(E.policy(E.name(self._name)))
        return xml

    def _xml_at_res(self, xml):
        return xml.find('.//policy/policy')

    def _xml_to_py(self, as_xml, to_py):
        Resource._r_has_xml_status(as_xml, to_py)
        Resource.copyifexists(as_xml, 'description', to_py)

        x_match = as_xml.find('match')
        x_then = as_xml.find('then')

        # collect up the 'match' criteria

        to_py['match_srcs'] = [
            this.text for this in x_match.findall('source-address')]
        to_py['match_dsts'] = [
            this.text for this in x_match.findall('destination-address')]
        to_py['match_apps'] = [
            this.text for this in x_match.findall('application')]

        # collect up the 'then' criteria

        to_py['action'] = x_then.xpath('permit | reject | deny')[0].tag

        if x_then.find('count') is not None:
            to_py['count'] = True
        if x_then.find('log/session-init') is not None:
            to_py['log_init'] = True
        if x_then.find('log/session-close') is not None:
            to_py['log_close'] = True

    # -------------------------------------------------------------------------
    # XML writing
    # -------------------------------------------------------------------------

    def _xml_change_action(self, xml):
        xml.append(E.then(E(self.should['action'])))
        return True

    def _xml_change_count(self, xml):
        xml.append(E.then(
            Resource.xmltag_set_or_del('count', self.should['count'])
        ))
        return True

    def _xml_change_log_init(self, xml):
        xml.append(E.then(E.log(
            Resource.xmltag_set_or_del('session-init', self.should['log_init'])
        )))
        return True

    def _xml_change_log_close(self, xml):
        xml.append(E.then(E.log(
            Resource.xmltag_set_or_del(
                'session-close',
                self.should['log_close'])
        )))
        return True

    def _xml_change_match_srcs(self, xml):
        adds, dels = Resource.diff_list(
            self.has['match_srcs'], self.should['match_srcs'])

        if len(adds):
            x_match = E.match()
            xml.append(x_match)
            for this in adds:
                x_match.append(E('source-address', E.name(this)))

        if len(dels):
            x_match = E.match()
            xml.append(x_match)
            for this in dels:
                x_match.append(E('source-address', JXML.DEL, E.name(this)))

        return True

    def _xml_change_match_dsts(self, xml):
        adds, dels = Resource.diff_list(
            self.has['match_dsts'], self.should['match_dsts'])

        if len(adds):
            x_match = E.match()
            xml.append(x_match)
            for this in adds:
                x_match.append(E('destination-address', E.name(this)))

        if len(dels):
            x_match = E.match()
            xml.append(x_match)
            for this in dels:
                x_match.append(
                    E('destination-address', JXML.DEL, E.name(this)))

        return True

    def _xml_change_match_apps(self, xml):
        adds, dels = Resource.diff_list(
            self.has['match_apps'], self.should['match_apps'])

        if len(adds):
            x_match = E.match()
            xml.append(x_match)
            for this in adds:
                x_match.append(E('application', E.name(this)))

        if len(dels):
            x_match = E.match()
            xml.append(x_match)
            for this in dels:
                x_match.append(E('application', JXML.DEL, E.name(this)))

        return True

    # -----------------------------------------------------------------------
    # Resource List, Catalog
    # -- only executed by 'manager' resources
    # -----------------------------------------------------------------------

    def _r_list(self):
        got = self.P._xml_config_read()
        self._rlist = [
            this.text for this in got.xpath('.//policy/policy/name')]

    def _r_catalog(self):
        got = self.D.rpc.get_config(self.P._xml_at_top())
        policies = got.find('.//security/policies/policy')
        for pol in policies.findall('policy'):
            name = pol.find('name').text
            self._rcatalog[name] = {}
            self._xml_to_py(pol, self._rcatalog[name])
