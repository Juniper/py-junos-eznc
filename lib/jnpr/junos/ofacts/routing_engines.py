import re as RE


def _get_vc_status(dev, facts):
    try:
        rsp = dev.rpc.get_virtual_chassis_information()
        # MX issue where command returns, but without content
        if rsp is not True:
            facts["vc_capable"] = True
            return rsp
        else:
            facts["vc_capable"] = False
            return None
    except:
        facts["vc_capable"] = False
        return None


def facts_routing_engines(junos, facts):

    re_facts = ["mastership-state", "status", "model", "up-time", "last-reboot-reason"]

    master = []

    vc_info = _get_vc_status(junos, facts)

    if vc_info is not None:
        facts["vc_mode"] = vc_info.findtext(".//virtual-chassis-mode")
        if (
            len(vc_info.xpath(".//virtual-chassis-id-information" "[@style='fabric']"))
            > 0
        ):
            facts["vc_fabric"] = True
        vc_list = vc_info.xpath(
            ".//member-role[starts-with(.,'Master') " "or starts-with(.,'Backup')]"
        )
        if len(vc_list) > 1:
            facts["2RE"] = True
        for member_id in vc_info.xpath(
            ".//member-role[starts-with(.,'Master')]" "/preceding-sibling::member-id"
        ):
            master.append("RE{}".format(member_id.text))

    try:
        re_info = junos.rpc.get_route_engine_information()
    except:
        # this means that the RPC failed.  this should "never"
        # happen, but we will trap it cleanly for now
        return

    re_list = re_info.xpath(".//route-engine")

    if len(re_list) > 1:
        facts["2RE"] = True

    for re in re_list:
        x_re_name = re.xpath("ancestor::multi-routing-engine-item/re-name")

        if not x_re_name:
            # not a multi-instance routing engine platform, but could
            # have multiple RE slots
            re_name = "RE"
            x_slot = re.find("slot")
            slot_id = x_slot.text if x_slot is not None else "0"
            re_name = re_name + slot_id
        else:
            # multi-instance routing platform
            m = RE.search("(\d)", x_re_name[0].text)
            if vc_info is not None:
                # => RE0-RE0 | RE0-RE1
                re_name = "RE{}-RE{}".format(m.group(0), re.find("slot").text)
            else:
                re_name = "RE" + m.group(0)  # => RE0 | RE1

        re_fd = {}
        facts[re_name] = re_fd
        for factoid in re_facts:
            x_f = re.find(factoid)
            if x_f is not None:
                re_fd[factoid.replace("-", "_")] = x_f.text

        if vc_info is None and "mastership_state" in re_fd:
            if facts[re_name]["mastership_state"] == "master":
                master.append(re_name)

    # --[ end for-each 're' ]-------------------------------------------------

    len_master = len(master)
    if len_master > 1:
        facts["master"] = master
    elif len_master == 1:
        facts["master"] = master[0]
