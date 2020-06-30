from jnpr.junos.exception import RpcError


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {
        "switch_style": "A string which indicates the Ethernet "
        "switching syntax style supported by the device. "
        "Possible values are: 'BRIDGE_DOMAIN', 'VLAN', "
        "'VLAN_L2NG', or 'NONE'.",
    }


def get_facts(device):
    """
    Gathers facts about the Ethernet switching configuration syntax style.
    """
    switch_style = None

    try:
        # RPC if VLAN style (Older EX, QFX, and SRX)
        # or if VLAN_L2NG (aka ELS) style (Newer EX and QFX)
        rsp = device.rpc.get_ethernet_switching_table_information(summary=True)
        if rsp.tag == "l2ng-l2ald-rtb-macdb":
            switch_style = "VLAN_L2NG"
        elif rsp.tag == "ethernet-switching-table-information":
            switch_style = "VLAN"
    except RpcError:
        pass

    if switch_style is None:
        try:
            # CLI command for MX style. Using the CLI command instead of the
            # RPC because PTX lies. It returns <l2ald-rtb-mac-count> for the
            # RPC, but doesn't really support bridging. It raises an RPC
            # error for the CLI command (via <command> RPC), so we use
            # the CLI command to make sure the device really does support
            # bridge domains. In this case, an RpcError is raised with a
            # bad_element of 'bridge'.
            #
            # However, on the backup RE for devices that really do support
            # bridge domains, we get an RpcError stating:
            # 'the l2-learning subsystem is not running'
            rsp = device.rpc.cli(
                "show bridge mac-table count", format="xml", normalize=True
            )
            if rsp.tag == "l2ald-rtb-mac-count":
                switch_style = "BRIDGE_DOMAIN"
            else:
                switch_style = "NONE"
        except RpcError as err:
            # Probably a PTX.
            if err.rpc_error["bad_element"] == "bridge":
                switch_style = "NONE"
            # Probably a non-master RE on an MX.
            elif err.rpc_error["message"] == "the l2-learning subsystem is not running":
                switch_style = "BRIDGE_DOMAIN"

    return {
        "switch_style": switch_style,
    }
