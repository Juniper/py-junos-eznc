from jnpr.junos.exception import ConnectNotMasterError
from jnpr.junos.exception import RpcError


def facts_chassis(junos, facts):
    """
    The following facts are assigned:
      facts['2RE'] : designates if the device can support two RE, not that it
                     has them
      facts['RE_hw_mi'] : designates if the device is
                          multi-instance-routing-engine
      facts['model'] : product model
      facts['serialnumber'] : serial number

    NOTES:
        (1) if in a 2RE system, this routine will only load the information
            from the first chassis item.
        (2) hostname, domain, and fqdn are retrieved from configuration data;
            inherited configs are checked.
    """
    # Set default values.
    facts["2RE"] = False
    facts["RE_hw_mi"] = False
    facts["model"] = "UNKNOWN"
    facts["serialnumber"] = "UNKNOWN"

    rsp = junos.rpc.get_chassis_inventory()
    if rsp.tag == "error":
        raise RuntimeError()

    if rsp.tag == "output":
        # this means that there was an error; due to the
        # fact that this connection is not on the master
        # @@@ need to validate on VC-member
        raise ConnectNotMasterError(junos)

    if rsp.tag == "multi-routing-engine-results":
        facts["2RE"] = True
        facts["RE_hw_mi"] = True
    else:
        facts["2RE"] = False

    facts["model"] = rsp.findtext(".//chassis[1]/description", "UNKNOWN")
    facts["serialnumber"] = (
        rsp.findtext(".//chassis[1]/serial-number")
        or rsp.findtext('.//chassis-module[name="Backplane"]/serial-number')
        or rsp.findtext('.//chassis-module[name="Midplane"]/serial-number', "UNKNOWN")
    )

    if facts["model"] == "UNKNOWN" or facts["serialnumber"] == "UNKNOWN":
        raise RpcError()
