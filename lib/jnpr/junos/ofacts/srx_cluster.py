def facts_srx_cluster(junos, facts):
    # we should check the 'cluster status' on redundancy group 0 to see who is
    # master.  we use a try/except block for cases when SRX is not clustered

    try:
        cluster_st = junos.rpc.get_chassis_cluster_status(redundancy_group="0")
        if "error" == cluster_st.tag:
            facts["srx_cluster"] = False
            return

        primary = cluster_st.xpath('.//redundancy-group-status[.="primary"]')[0]

        node = primary.xpath("preceding-sibling::device-name[1]")[0].text.replace(
            "node", "RE"
        )

        if not facts.get("master"):
            facts["master"] = node
        elif node not in facts["master"]:
            facts["master"].append(node)

        facts["srx_cluster"] = True

    except:
        # this device doesn't support SRX chassis clustering; i.e.
        # since we arbitrarily execute the RPC on all devices, if we
        # hit this exception we just ignore, A-OK, yo!
        pass
