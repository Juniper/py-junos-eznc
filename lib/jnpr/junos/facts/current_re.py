

def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'current_re': 'A list', }


def get_facts(device):
    """
    Gathers facts from the <file-list/> RPC.
    """
    current_re = None

    rsp = device.rpc.get_interface_information(
              normalize=True,
              routing_instance='__juniper_private1__',
              terse=True, )
    for ifa in rsp.iterfind(".//address-family[address-family-name='inet']/"
                            "interface-address/ifa-local"):
        ifa_text = ifa.text
        if ifa_text is not None:
            (ip,_,_) = ifa.text.partition('/')
            if ip is not None:
                if ip in device.facts['_iri_hostname']:
                    if current_re is None:
                        # Make a copy, not a reference
                        current_re = list(device.facts['_iri_hostname'][ip])
                    else:
                        for host in device.facts['_iri_hostname'][ip]:
                            if host not in current_re:
                                current_re.append(host)

    return {'current_re': current_re, }
