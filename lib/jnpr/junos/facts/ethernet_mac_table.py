from jnpr.junos.exception import RpcError

def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'switch_style': "A string which indicates the Ethernet "
                            "switching syntax style supported by the device. "
                            "Possible values are: 'BRIDGE_DOMAIN', 'VLAN', "
                            "'VLAN_L2NG', or 'NONE'.", }


def get_facts(device):
    """
    Gathers facts about the Ethernet switching configuration syntax style.
    """
    switch_style = None

    try:
        # RPC if VLAN style (Older EX, QFX, and SRX)
        # or if VLAN_L2NG (aka ELS) style (Newer EX and QFX)
        rsp = device.rpc.get_ethernet_switching_table_information(summary=True)
        if rsp.tag == 'l2ng-l2ald-rtb-macdb':
            switch_style = 'VLAN_L2NG'
        elif rsp.tag == 'ethernet-switching-table-information':
            switch_style = 'VLAN'
    except RpcError:
        pass

    if switch_style is None:
        try:
            # RPC for MX style
            rsp = device.rpc.get_bridge_mac_table(count=True)
            if rsp.tag == 'l2ald-rtb-mac-count':
                switch_style = 'BRIDGE_DOMAIN'
            else:
                switch_style = 'NONE'
        except RpcError:
            switch_style = 'NONE'

    return {'switch_style': switch_style, }
