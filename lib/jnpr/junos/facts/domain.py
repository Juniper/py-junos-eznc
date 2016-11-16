from lxml import etree
from jnpr.junos.exception import PermissionError
from jnpr.junos.utils.fs import FS

def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'domain': "The domain name configured at [edit system domain-name] "
                      "configuration hierarchy.",
            'fqdn' : "The device's hostname + domain",}

def get_facts(device):
    """
    Gathers domain facts from the configuration or /etc/resolv.conf.
    """
    domain_config = """
        <configuration>
            <system>
                <domain-name/>
             </system>
        </configuration>
    """
    domain = None
    fqdn = None
    # Try to read the domain-name from the config.
    # This might fail due to lack of permissions.
    try:
        rsp = device.rpc.get_config(filter_xml=etree.XML(domain_config),
                                    options={'database': 'committed',
                                             'inherit': 'inherit',
                                             'commit-scripts': 'apply',})
        domain = rsp.findtext('.//domain-name')
    except PermissionError:
        pass

    if domain is None:
        fs = FS(device)
        file_content = (fs.cat('/etc/resolv.conf') or
                        fs.cat('/var/etc/resolv.conf'))
        words = file_content.split() if file_content is not None else []
        if 'domain' in words:
            idx = words.index('domain') + 1
            domain = words[idx]

    if domain:
        hostname = device.facts['hostname']
        if hostname:
            fqdn = hostname + '.' + domain

    return {'domain': domain,
            'fqdn': fqdn,}