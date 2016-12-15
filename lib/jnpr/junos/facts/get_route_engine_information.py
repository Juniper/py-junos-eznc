def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'2RE': "A boolean indicating if the device has more than one "
                   "Routing Engine installed.",
            'master': "On a single chassis/node system, FILL THIS IN",
            'RE0': "A dictionary with information about RE0 (if present). The "
                   "keys of the dictionary are: mastership_state, status, "
                   "model, up_time, and last_reboot_reason.",
            'RE1': "A dictionary with information about RE1 (if present). The "
                   "keys of the dictionary are: mastership_state, status, "
                   "model, up_time, and last_reboot_reason.",
            'RE_info': "A three-level dictionary with information about "
                       "the Routing Engines in the device. The first-level "
                       "key is the chassis or node name. The second-level key "
                       "is the slot number, the third keys are: "
                       "mastership_state, status, model, and "
                       "last_reboot_reason. A first-level key with a value "
                       "of 'default' will always be present and represents "
                       "the first node/chassis of the system. A second-level "
                       "key with a value of 'default' will always be present "
                       "for the default node/chassis and represents the "
                       "first Routing Engine on the first node/chassis. "
                       "When the second-level key is an integer number, it "
                       "will be present as both a string and an integer "
                       "so that the user doesn't have to worry about "
                       "converting between string and integer.", }


def get_facts(device):
    """
    Gathers facts from the <get-route-engine-information/> RPC.
    """
    multi_re = None
    master = None
    RE0 = None
    RE1 = None
    RE_info = None

    rsp = device.rpc.get_route_engine_information(normalize=True)
    re_list = rsp.findall('.//route-engine')
    if len(re_list) > 1:
        multi_re = True
    else:
        multi_re = False

    first_node = None
    first_slot = None
    for current_re in re_list:
        node = current_re.findtext('../../re-name')
        slot = current_re.findtext('slot')
        info = {'mastership_state': current_re.findtext('mastership-state'),
                'status': current_re.findtext('status'),
                'model': current_re.findtext('model'),
                'last_reboot_reason':
                    current_re.findtext('last-reboot-reason'),
                # This key is only returned in the RE0 and RE1 facts in order
                # to maintain backwards compatibility with the old fact
                # gathering system. Since the up_time value changes, it's not
                # really a "fact" and is therefore omitted from the new RE_info
                # fact.
                'up_time':
                    current_re.findtext('up-time'), }
        if node is None:
            node = 'default'
        if first_node is None:
            first_node = node
            first_slot = slot
        if node == first_node:
            if slot == '0' and RE0 is None:
                # Copy the dictionary
                RE0 = dict(info)
            if slot == '1' and RE1 is None:
                # Copy the dictionary
                RE1 = dict(info)
        # Don't want the up_time key in the new RE_info fact.
        if 'up_time' in info:
            del info['up_time']
        if RE_info is None:
            RE_info = {}
        if not node in RE_info:
            RE_info[node] = {}
        RE_info[node][slot] = info
        # Try to also save with the second-level key as a number.
        try:
            slot_num = int(slot)
            RE_info[node][slot_num] = info
        except ValueError:
            pass
    if first_node is not None and first_node != 'default':
        RE_info['default'] = RE_info[first_node]
    if first_slot is not None:
        RE_info['default']['default']= RE_info['default'][first_slot]

    return {'2RE': multi_re,
            'master': master,
            'RE0': RE0,
            'RE1': RE1,
            'RE_info': RE_info, }
