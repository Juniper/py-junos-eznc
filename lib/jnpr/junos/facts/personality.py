import re

def facts_personality(junos, facts):

    model = facts['model']

    if model != 'Virtual Chassis':
        examine = model
    else:
        for fact in facts:
            if re.match("^RE\d", fact):
                examine = facts[fact]['model']
                break

    examine = examine.upper()

    if re.match("^(EX)|(QFX)", examine):
        persona = 'SWITCH'
    elif examine.startswith("MX"):
        persona = 'MX'
    elif examine.startswith('VMX'):
        facts['virtual'] = True
        persona = 'MX'
    elif examine.startswith("VJX"):
        facts['virtual'] = True
        persona = 'SRX_BRANCH'
    elif 'VRR' == examine:
        persona = "MX"
        facts['virtual'] = True
    elif examine.startswith("M"):
        persona = "M"
    elif examine.startswith("T"):
        persona = "T"
    elif examine.startswith("PTX"):
        persona = "PTX"
    elif re.match("SRX\s?(\d){4}", examine):
        persona = 'SRX_HIGHEND'
    elif re.match("SRX\s?(\d){3}", examine):
        persona = 'SRX_BRANCH'
    elif re.search("firefly", examine, re.IGNORECASE):
        facts['virtual'] = True
        persona = 'SRX_BRANCH'
    elif 'OLIVE' == examine:
        facts['virtual'] = True
        persona = 'OLIVE'
    else:
        persona = "UNKNOWN"

    facts['personality'] = persona
