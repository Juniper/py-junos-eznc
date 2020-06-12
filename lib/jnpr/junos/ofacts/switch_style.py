import re


def facts_switch_style(junos, facts):
    persona = facts["personality"]

    if persona in ["MX", "SRX_HIGHEND"]:
        style = "BRIDGE_DOMAIN"
    elif persona in ["SWITCH", "SRX_BRANCH"]:
        model = facts["model"]
        if re.match("firefly", model, re.IGNORECASE):
            style = "NONE"
        elif re.match("^(EX9)|(EX43)", model):
            style = "VLAN_L2NG"
        else:
            style = "VLAN"
    else:
        style = "NONE"

    facts["switch_style"] = style
