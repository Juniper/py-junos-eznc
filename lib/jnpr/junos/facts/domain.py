from jnpr.junos.utils.fs import FS


def facts_domain(junos, facts):
    """
    The following facts are required:
        facts['hostname']

    The following facts are assigned:
        facts['domain']
        facts['fqdn']
    """
    fs = FS(junos)
    # changes done to fix issue #332
    file_content = fs.cat('/etc/resolv.conf') or fs.cat('/var/etc/resolv.conf')
    words = file_content.split() if file_content is not None else ''
    if 'domain' not in words:
        facts['domain'] = None
        facts['fqdn'] = facts['hostname']
    else:
        idx = words.index('domain') + 1
        facts['domain'] = words[idx]
        facts['fqdn'] = facts['hostname'] + '.' + facts['domain']
