from jnpr.junos.exception import RpcError


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {
        "srx_cluster": "A boolean indicating if the device is part of an "
        "SRX cluster.",
        "srx_cluster_id": "A string containing the configured cluster id",
        "srx_cluster_redundancy_group": "A multi-level dictionary of "
        "information about the SRX "
        "cluster redundancy groups "
        "on the device. The first-level "
        "key is the redundancy group id. "
        "The second-level keys are: "
        "cluster_id, failover_count, "
        "node0, and node1. The node0 and "
        "node1 keys have third-level keys "
        "of priority, preempt, status, "
        "and failover_mode. The values "
        "for this fact correspond to the "
        "values of the 'show chassis "
        "cluster status' CLI command.",
    }


def get_facts(device):
    """
    Gathers facts from the <get-chassis-cluster-status/> RPC.
    """
    srx_cluster = None
    srx_cluster_id = None
    redundancy_group = None

    try:
        rsp = device.rpc.get_chassis_cluster_status(normalize=True)
        if rsp is not None:
            if rsp.tag == "error":
                srx_cluster = False
            else:
                srx_cluster = True
                srx_cluster_id = rsp.findtext("cluster-id")
                groups = rsp.findall("redundancy-group")
                if groups is not None:
                    redundancy_group = {}
                    for group in groups:
                        group_id = group.findtext("redundancy-group-id")
                        redundancy_group[group_id] = {
                            "cluster_id": group.findtext("cluster-id"),
                            "failover_count": group.findtext(
                                "redundancy-group-failover-count"
                            ),
                        }
                        # Iterate over the broken XML in <device-stats>
                        for stats in group.findall("./device-stats"):
                            for node in zip(
                                stats.findall("device-name"),
                                stats.findall("device-priority"),
                                stats.findall("redundancy-group-status"),
                                stats.findall("preempt"),
                                stats.findall("failover-mode"),
                                stats.findall("monitor-failures"),
                            ):
                                redundancy_group[group_id][node[0].text] = {
                                    "priority": node[1].text,
                                    "status": node[2].text,
                                    "preempt": node[3].text,
                                    "failover_mode": node[4].text,
                                    "monitor-failures": node[5].text,
                                }
    except RpcError:
        # Likely a device that doesn't implement the
        # <get-chassis-cluster-status/> RPC.
        # That's OK. Just ignore it and leave srx_cluster = None.
        pass
    return {
        "srx_cluster": srx_cluster,
        "srx_cluster_id": srx_cluster_id,
        "srx_cluster_redundancy_group": redundancy_group,
    }
