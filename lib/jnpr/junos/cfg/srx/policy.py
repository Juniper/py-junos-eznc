# 3rd-party modules
from lxml.builder import E

# module packages
from jnpr.junos.cfg.srx.policy_rule import PolicyRule
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML


class PolicyContext(Resource):

    """
    [edit security policy from-zone <from_zone> to-zone <to_zone>]

    Resource name: tuple(from_zone, to_zone)
      <from_zone>  is the name of the From zone
      <to_zone> is the name of the To zone

    Manages Resources:
      rule, PolicyRule
    """

    PROPERTIES = [
        '$rules',
        '$rules_count'
    ]

    def __init__(self, junos, name=None, **kvargs):
        if name is None:
            # resource-manager
            Resource.__init__(self, junos, name, **kvargs)
            return

        # specific instance will manage policy rules
        self.rule = PolicyRule(junos, M=self, parent=self)
        self._manages = ['rule']
        self._name_from_zone = name[0]
        self._name_to_zone = name[1]
        Resource.__init__(self, junos, name, **kvargs)

    def _xml_at_top(self):
        return E.security(E.policies(
            E.policy(
                E('from-zone-name', self._name_from_zone),
                E('to-zone-name', self._name_to_zone)
            )))

    # -------------------------------------------------------------------------
    # XML reading
    # -------------------------------------------------------------------------

    def _xml_config_read(self):
        """
          ~! OVERLOADS !~
        """
        xml = self._xml_at_top()
        xml.find('.//policy').append(E.policy(JXML.NAMES_ONLY))
        return self._junos.rpc.get_config(xml)

    def _xml_at_res(self, xml):
        return xml.find('.//policy')

    def _xml_to_py(self, as_xml, to_py):
        Resource._r_has_xml_status(as_xml, to_py)
        to_py['$rules'] = [
            policy.text for policy in as_xml.xpath('.//policy/name')]
        to_py['$rules_count'] = len(to_py['$rules'])

    # -----------------------------------------------------------------------
    # Resource List, Catalog
    # -- only executed by 'manager' resources
    # -----------------------------------------------------------------------

    def _r_list(self):
        """
          build the policy context resource list from the command:
          > show security policies zone-context
        """
        got = self._junos.rpc.get_firewall_policies(zone_context=True)

        for pc in got.xpath('//policy-zone-context/policy-zone-context-entry'):
            from_zone = pc.find('policy-zone-context-from-zone').text
            to_zone = pc.find('policy-zone-context-to-zone').text
            self._rlist.append((from_zone, to_zone))

    def _r_catalog(self):
        got = self._junos.rpc.get_firewall_policies(zone_context=True)

        for pc in got.xpath('//policy-zone-context/policy-zone-context-entry'):
            from_zone = pc.find('policy-zone-context-from-zone').text
            to_zone = pc.find('policy-zone-context-to-zone').text
            count = int(pc.find('policy-zone-context-policy-count').text)
            self._rcatalog[(from_zone, to_zone)] = {'$rules_count': count}
