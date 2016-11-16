def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'model': "An uppercase string containing the device's model.",
            'hostname': 'A string containing the hostname of the device.',}

def get_facts(device):
    """
    Gathers facts from the <get-software-information/> RPC.
    """
    rsp = device.rpc.get_software_information()

    model = rsp.findtext('.//product-model')
    if model:
        # Capitalize for consistency with the previous model fact that
        # was returned from the chassis information and was (usually?) in upper
        # case.
        model = model.upper()

    hostname = rsp.findtext('.//host-name')

    return {'model': model,
            'hostname': hostname}