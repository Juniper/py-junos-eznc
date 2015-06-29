from jnpr.junos.utils.fs import FS
from jnpr.junos.exception import RpcError
from jnpr.junos.jxml import INHERIT
from lxml.builder import E


def facts_domain(junos, facts):
    """
    The following facts are required:
        facts['hostname']

    The following facts are assigned:
        facts['domain']
        facts['fqdn']
    """

    try:
        domain_filter_xml = E('configuration', E('system', E('domain-name')))
        domain = junos.rpc.get_config(filter_xml=domain_filter_xml, options=INHERIT)
        domain_name = domain.xpath('.//domain-name')
        if len(domain_name) > 0:
            facts['domain'] = domain_name[0].text
            facts['fqdn'] = facts['hostname'] + '.' + facts['domain']
            return
    except RpcError:
        pass

    fs = FS(junos)
    file_content = fs.cat('/etc/resolv.conf') or fs.cat('/var/etc/resolv.conf')
    words = file_content.split() if file_content is not None else ''
    if 'domain' not in words:
        facts['domain'] = None
        facts['fqdn'] = facts['hostname']
    else:
        idx = words.index('domain') + 1
        facts['domain'] = words[idx]
        facts['fqdn'] = facts['hostname'] + '.' + facts['domain']
