from jnpr.junos.exception import RpcError


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {
        "vc_capable": "A boolean indicating if the device is currently "
        "configured in a virtual chassis. In spite of the "
        "name, this fact does NOT indicate whether or not "
        "the device is CAPABLE of joining a VC.",
        "vc_mode": "A string indicating the current virtual chassis "
        "mode of the device.",
        "vc_fabric": "A boolean indicating if the device is currently in "
        "fabric mode.",
        "vc_master": "A string indicating the chassis/node which is "
        "currently the master of the VC.",
    }


def get_facts(device):
    """
    Gathers facts from the <get-virtual-chassis-information/> RPC.
    """
    vc_capable = None
    vc_mode = None
    vc_fabric = None
    vc_master = None

    try:
        rsp = device.rpc.get_virtual_chassis_information(normalize=True)
        # MX issue where command returns, but without content. In this case,
        # rsp is set to True.
        if rsp is not True:
            vc_capable = True
            if rsp is not None:
                vc_mode = rsp.findtext(".//virtual-chassis-mode")
                vc_id_info = rsp.find(".//virtual-chassis-id-information")
                if vc_id_info is not None:
                    if vc_id_info.get("style") == "fabric":
                        vc_fabric = True
                    else:
                        vc_fabric = False
                for member_id in rsp.xpath(
                    ".//member-role[starts-with(.,'Master')]"
                    "/preceding-sibling::member-id"
                ):
                    if vc_master is None:
                        vc_master = member_id.text
                    else:
                        old_vc_master = vc_master
                        vc_master = None
                        raise ValueError(
                            "Member %s and member %s both claim "
                            "to be master of the VC." % (old_vc_master, member_id.text)
                        )
        else:
            vc_capable = False
    except RpcError:
        # Likely a device that doesn't implement the
        # <get-virtual-chassis-information/> RPC.
        # That's OK. Set vc_capable = False.
        vc_capable = False

    return {
        "vc_capable": vc_capable,
        "vc_mode": vc_mode,
        "vc_fabric": vc_fabric,
        "vc_master": vc_master,
    }
