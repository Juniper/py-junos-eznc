def facts_ifd_style(junos, facts):
    persona = facts["personality"]
    if persona == "SWITCH":
        facts["ifd_style"] = "SWITCH"
    else:
        facts["ifd_style"] = "CLASSIC"
