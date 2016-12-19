import re


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'ifd_style': "The type of physical interface (ifd) supported by "
                         "the device. Choices are 'CLASSIC' or 'SWITCH'.", }


def get_facts(device):
    """
    Determines ifd_style fact based on the personality.
    """
    ifd_style = 'CLASSIC'

    if device.facts['personality'] == 'SWITCH':
        ifd_style = 'SWITCH'

    return {'ifd_style': ifd_style, }
