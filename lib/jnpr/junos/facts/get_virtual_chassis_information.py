from jnpr.junos.exception import RpcError


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'vc_capable': "A boolean indicating if the device is currently "
                          "configured in a virtual chassis. In spite of the "
                          "name, this fact does NOT indicate whether or not "
                          "the device is CAPABLE of joining a VC.",
            'vc_mode': "A string indicating the current virtual chassis "
                       "mode of the device.",
            'vc_fabric': "A boolean indicating if the device is currently in "
                         "fabric mode.", }


def get_facts(device):
    """
    Gathers facts from the <get-virtual-chassis-information/> RPC.
    """
    vc_capable = None
    vc_mode = None
    vc_fabric = None
    try:
        rsp = device.rpc.get_virtual_chassis_information(normalize=True)
        # MX issue where command returns, but without content. In this case,
        # rsp is set to True.
        if rsp is not True:
            vc_capable = True
            if rsp is not None:
                vc_mode = rsp.findtext('.//virtual-chassis-mode')
                vc_id_info = rsp.find('.//virtual-chassis-id-information')
                if vc_id_info:
                    if vc_id_info.get('style') == 'fabric':
                        vc_fabric = True
                    else:
                        vc_fabric = False
        else:
            vc_capable = False
    except RpcError:
        # Likely a device that doesn't implement the
        # <get-virtual-chassis-information/> RPC.
        # That's OK. Set vc_capable = False.
        vc_capable = False
    return {'vc_capable': vc_capable,
            'vc_mode': vc_mode,
            'vc_fabric': vc_fabric, }
