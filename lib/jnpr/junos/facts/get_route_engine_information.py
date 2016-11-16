def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'2RE': "A boolean indicating if the device has more than one "
                   "Routing Engine installed.",}

def get_facts(device):
    """
    Gathers facts from the <get-route-engine-information/> RPC.
    """
    multi_re = None
    rsp = device.rpc.get_route_engine_information()
    re_list = rsp.findall('.//route-engine')
    if len(re_list) > 1:
        multi_re = True
    else:
        multi_re = False

    return {'2RE': multi_re,}