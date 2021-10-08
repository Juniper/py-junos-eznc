from jnpr.junos.exception import ConnectNotMasterError
from jnpr.junos.exception import RpcError


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {
        "RE_hw_mi": "(Routing Engine hardware multi-instance) A boolean "
        "indicating if this is a multi-chassis system.",
        "serialnumber": "A string containing the serial number of the "
        "device's chassis. If there is no chassis serial "
        "number, the serial number of the backplane or "
        "midplane is returned.",
    }


def get_facts(device):
    """
    Gathers facts from the <get-chassis-inventory/> RPC.
    """
    rsp = device.rpc.get_chassis_inventory(normalize=True)
    if rsp.tag == "error":
        raise RpcError()

    if (
        rsp.tag == "output"
        and rsp.text.find("can only be used on the master routing engine") != -1
    ):
        # An error; due to the fact that this RPC can only be executed on the
        # master Routing Engine
        raise ConnectNotMasterError()

    RE_hw_mi = False
    if rsp.tag == "multi-routing-engine-results":
        RE_hw_mi = True

    serialnumber = (
        rsp.findtext(".//chassis[1]/serial-number")
        or rsp.findtext('.//chassis-module[name="Backplane"]/serial-number')
        or rsp.findtext('.//chassis-module[name="Midplane"]/serial-number')
    )

    return {
        "RE_hw_mi": RE_hw_mi,
        "serialnumber": serialnumber,
    }
