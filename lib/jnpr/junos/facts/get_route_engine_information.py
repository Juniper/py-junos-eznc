def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {
        "2RE": "A boolean indicating if the device has more than one "
        "Routing Engine installed.",
        "master": "On a single chassis/node system, a string value of "
        "'RE0' or 'RE1' indicating which RE is master. On a "
        "multi-chassis or multi-node system, the value is a "
        "list of these strings indicating whether RE0 or RE1 "
        "is master. There is one entry in the list for each "
        "chassis/node in the system.",
        "RE0": "A dictionary with information about RE0 (if present). The "
        "keys of the dictionary are: mastership_state, status, "
        "model, up_time, and last_reboot_reason.",
        "RE1": "A dictionary with information about RE1 (if present). The "
        "keys of the dictionary are: mastership_state, status, "
        "model, up_time, and last_reboot_reason.",
        "re_info": "A three-level dictionary with information about "
        "the Routing Engines in the device. The first-level "
        "key is the chassis or node name. The second-level key "
        "is the slot number, the third-level keys are: "
        "mastership_state, status, model, and "
        "last_reboot_reason. A first-level key with a value "
        "of 'default' will always be present and represents "
        "the first chassis/node of the system (Note: the first "
        "chasis/node of the system is not necessarily the "
        "'master' node in a VC.) A second-level key with a "
        "value of 'default' will always be present "
        "for the default chassis/node and represents the "
        "first Routing Engine on the first node/chassis. "
        "(Note: the first RE of a chassis/node is not "
        "necessarily the 'master' RE of the chassis/node. See "
        "the RE_master fact for info on the 'master' RE of "
        "each chassis/node.)",
        "re_master": "A dictionary indicating which RE slot is master for "
        "each chassis/node in the system. The dictionary key "
        "is the chassis or node name. A key with a value "
        "of 'default' will always be present and represents "
        "the first node/chassis of the system. (Note: the "
        "first chassis/node of the system is not necessarily "
        "the 'master' node in a VC. See the vc_master fact "
        "to determine which chassis/node is the master of "
        "a VC.)",
    }


def get_facts(device):
    """
    Gathers facts from the <get-route-engine-information/> RPC.
    """
    multi_re = None
    master = None
    RE0 = None
    RE1 = None
    re_info = None
    re_master = None

    rsp = device.rpc.get_route_engine_information(normalize=True)
    re_list = rsp.findall(".//route-engine")
    if len(re_list) > 1:
        multi_re = True
    else:
        multi_re = False

    first_node = None
    first_slot = None
    master_list = []
    node_masters = {}
    for current_re in re_list:
        node = current_re.findtext("../../re-name", "default")
        slot = current_re.findtext("slot", "0")
        info = {
            "mastership_state": current_re.findtext("mastership-state", "master"),
            "status": current_re.findtext("status"),
            "model": current_re.findtext("model"),
            "last_reboot_reason": current_re.findtext("last-reboot-reason"),
            # This key is only returned in the RE0 and RE1 facts in order
            # to maintain backwards compatibility with the old fact
            # gathering system. Since the up_time value changes, it's not
            # really a "fact" and is therefore omitted from the new re_info
            # fact.
            "up_time": current_re.findtext("up-time"),
        }
        if first_node is None:
            first_node = node
            first_slot = slot
        if node == first_node:
            if slot == "0" and RE0 is None:
                # Copy the dictionary
                RE0 = dict(info)
            if slot == "1" and RE1 is None:
                # Copy the dictionary
                RE1 = dict(info)
        # Don't want the up_time key in the new re_info fact.
        if "up_time" in info:
            del info["up_time"]
        if re_info is None:
            re_info = {}
        if node not in re_info:
            re_info[node] = {}
        # Save with second-level key as a string.
        re_info[node][slot] = info
        # If it's a master RE, then save in node_masters and master_list
        if "mastership_state" in info and info["mastership_state"].lower().startswith(
            "master"
        ):
            node_masters[node] = slot
            master_list.append("RE" + slot)
    # Fill in the 'default' first-level key if multi-chassis/node system
    if first_node is not None and first_node != "default":
        re_info["default"] = re_info[first_node]
        if first_node in node_masters:
            node_masters["default"] = node_masters[first_node]
    # Fill in the 'default' second-level key if at least one RE was found.
    if first_slot is not None:
        re_info["default"]["default"] = re_info["default"][first_slot]

    # Set the 'master' fact to a string or list based on the number of members.
    master_list_len = len(master_list)
    if master_list_len == 1:
        master = master_list[0]
    elif master_list_len > 1:
        master = master_list

    # If any info in the node_masters dict, then return it as fact 're_master'
    if node_masters:
        re_master = node_masters

    return {
        "2RE": multi_re,
        "master": master,
        "RE0": RE0,
        "RE1": RE1,
        "re_info": re_info,
        "re_master": re_master,
    }
