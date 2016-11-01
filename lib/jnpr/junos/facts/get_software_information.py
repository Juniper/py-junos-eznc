def provides_facts():
    """
    Doc String details.
    Returns:

    """
    return ('model',)

def get_facts(device):
    """
    Doc String details.
    """
    rsp = device.rpc.get_software_information()

    model = rsp.findtext('.//product-model')
    if model:
        # Capitalize for consistency with the previous model fact that
        # was returned from the chassis information and was (usually?) in upper
        # case.
        model = model.upper()

    return {'model': model,}