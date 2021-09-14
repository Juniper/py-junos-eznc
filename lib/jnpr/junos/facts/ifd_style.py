def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {
        "ifd_style": "The type of physical interface (ifd) supported by "
        "the device. Choices are 'CLASSIC' or 'SWITCH'.",
    }


def get_facts(device):
    """
    Determines ifd_style fact based on the personality.
    """
    ifd_style = "CLASSIC"

    if device.facts["personality"] == "SWITCH":
        ifd_style = "SWITCH"
    elif device.facts["personality"] == "JDM":
        ifd_style = None

    return {
        "ifd_style": ifd_style,
    }
