from jnpr.junos.exception import RpcError


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'srx_cluster': "A boolean indicating if the device is part of an "
                           "SRX cluster.",
            'srx_cluster_id': "A string containing the configured cluster id"}


def get_facts(device):
    """
    Gathers facts from the <get-chassis-cluster-status/> RPC.
    """
    srx_cluster = None
    srx_cluster_id = None

    try:
        rsp = device.rpc.get_chassis_cluster_status(normalize=True,
                                                    redundancy_group="0")
        if rsp is not None:
            if rsp.tag == 'error':
                srx_cluster = False
            else:
                srx_cluster = True
                srx_cluster_id = rsp.findtext('./cluster-id')
    except RpcError:
        # Likely a device that doesn't implement the
        # <get-chassis-cluster-status/> RPC.
        # That's OK. Just ignore it and leave srx_cluster = None.
        pass
    return {'srx_cluster': srx_cluster,
            'srx_cluster_id': srx_cluster_id}
