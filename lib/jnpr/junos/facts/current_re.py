

def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'current_re': "A list of internal routing instance hostnames "
                          "for the current RE. These hostnames identify "
                          "things like the RE's slot ('re0' or 're1'), the "
                          "RE's mastership state ('master' or 'backup'), "
                          "and node in a VC ('member0' or 'member1')", }


def get_facts(device):
    """
    The RPC-equivalent of show interfaces terse on private routing instance.
    """
    current_re = None

    rsp = device.rpc.get_interface_information(
              normalize=True,
              routing_instance='__juniper_private1__',
              terse=True, )
    # Get the local IPv4 addresses from the response.
    for ifa in rsp.iterfind(".//address-family[address-family-name='inet']/"
                            "interface-address/ifa-local"):
        ifa_text = ifa.text
        if ifa_text is not None:
            # Separate the IP from the mask
            (ip, _, _) = ifa.text.partition('/')
            if ip is not None:
                # Use the _iri_hostname fact to map the IP address to
                # an internal routing instance hostname.
                if ip in device.facts['_iri_hostname']:
                    if current_re is None:
                        # Make a copy, not a reference
                        current_re = list(device.facts['_iri_hostname'][ip])
                    else:
                        for host in device.facts['_iri_hostname'][ip]:
                            if host not in current_re:
                                current_re.append(host)

    return {'current_re': current_re, }
