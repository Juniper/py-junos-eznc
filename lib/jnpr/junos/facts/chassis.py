from lxml.builder import E
from jnpr.junos import jxml as JXML


def chassis(junos, facts):
    """
    Obtain basic chassis facts:
      model : product model
      serialnumber : serial number
      hostname : host
      fqdn : fully-qualified domain-name
      domain : domain-name

    NOTES:
    (1) if in a 2RE system, this routine will only load the information
        from the first chassis item.
    (2) hostname, domain, and fqdn are retrieved from configuration data;
        inherited configs are checked.
    """
    rsp = junos.rpc.get_chassis_inventory()

    if rsp.tag == 'multi-routing-engine-results':
        facts['2RE'] = True
        x_ch = rsp.xpath('.//chassis-inventory')[0].find('chassis')
    else:
        facts['2RE'] = False
        x_ch = rsp.find('chassis')

    facts['model'] = x_ch.find('description').text
    try:
        facts['serialnumber'] = x_ch.find('serial-number').text
    except:
        # if the toplevel chassis does not have a serial-number, then
        # check the Backplane chassis-module
        facts['serialnumber'] = x_ch.xpath(
            'chassis-module[name="Backplane"]/serial-number')[0].text

    got = junos.rpc.get_config(
        E.system(
            E('host-name'),
            E('domain-name')
        ),
        JXML.INHERIT
    )

    hostname = got.find('.//host-name')
    facts['hostname'] = hostname.text if hostname is not None else 'Amnesiac'
    facts['fqdn'] = facts['hostname']

    domain = got.find('.//domain-name')
    if domain is not None:
        facts['domain'] = domain.text
        facts['fqdn'] += '.%s' % facts['domain']
    else:
        facts['domain'] = None
