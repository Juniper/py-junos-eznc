from lxml.builder import E
from jnpr.junos import jxml as JXML
from jnpr.junos.exception import ConnectNotMasterError

def facts_chassis(junos, facts):
    """
    The following facts are assigned:
      facts['model'] : product model
      facts['serialnumber'] : serial number

    NOTES:
        (1) if in a 2RE system, this routine will only load the information
            from the first chassis item.
        (2) hostname, domain, and fqdn are retrieved from configuration data;
            inherited configs are checked.
    """
    rsp = junos.rpc.get_chassis_inventory()
    if rsp.tag == 'output':
        # this means that there was an error; due to the
        # fact that this connection is not on the master
        # @@@ need to validate on VC-member
        raise ConnectNotMasterError(junos)

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


