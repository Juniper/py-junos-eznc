import re


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'personality': 'A string which is generally based on the '
                           'platform and indicates the behavior of the '
                           'device.',
            'virtual': 'A boolean indicating if the device is virtual.', }


def get_facts(device):
    """
    Determines personality fact based on the model.
    """
    personality = None
    virtual = None

    model = device.facts['model']

    if model == 'Virtual Chassis':
        # Set model to the model of the first RE in the multi-chassis system.
        model = device.facts['re_info']['default']['default']['model']

    if re.match('^(EX)|(QFX)', model):
        personality = 'SWITCH'
        virtual = False
    elif model.startswith('MX'):
        # The VMX has an RE type of 'RE-VMX'
        if (device.facts['re_info']['default']['default']['model'] ==
                'RE-VMX'):
            personality = 'MX'
            virtual = True
        else:
            personality = 'MX'
            virtual = False
    elif model.startswith('VMX'):
        personality = 'MX'
        virtual = True
    elif model.startswith('VJX'):
        personality = 'SRX_BRANCH'
        virtual = True
    elif 'VRR' == model:
        personality = 'MX'
        virtual = True
    elif model.startswith('M'):
        personality = 'M'
        virtual = False
    elif model.startswith('T'):
        personality = 'T'
        virtual = False
    elif model.startswith('PTX'):
        personality = 'PTX'
        # The vPTX has an RE type of 'RE-VIRTUAL'
        if (device.facts['re_info']['default']['default']['model'] ==
           'RE-VIRTUAL'):
            virtual = True
        else:
            virtual = False
    elif re.match('SRX\s?(\d){4}', model):
        personality = 'SRX_HIGHEND'
        virtual = False
    elif re.match('SRX\s?(\d){3}', model):
        personality = 'SRX_BRANCH'
        virtual = False
    elif re.search('firefly', model, re.IGNORECASE):
        personality = 'SRX_BRANCH'
        virtual = True
    elif 'OLIVE' == model:
        personality = 'OLIVE'
        virtual = True
    elif model.startswith('NFX'):
        personality = 'NFX'
        virtual = False

    return {'personality': personality,
            'virtual': virtual, }
