import re

def personality( junos, facts ):
  
  model = facts['model']

  examine = model if model != 'Virtual Chassis' else facts['RE0']['model']

  if re.match("^(EX)|(QFX)", examine):
    persona = 'SWITCH'
  elif examine.startswith("MX"):
    persona = 'MX'
  elif examine.startswith("vMX"):
    facts['virtual'] = True
    persona = 'MX'
  elif examine.startswith("VJX"):
    facts['virtual'] = True
    persona = 'SRX_BRANCH'
  elif examine.startswith("M"):
    persona = "M"
  elif re.match("SRX\s?(\d){4}", examine):
    persona = 'SRX_HIGHEND'    
  elif re.match("SRX\s?(\d){3}", examine):
    persona = 'SRX_BRANCH'
  elif re.search("firefly", examine, re.IGNORECASE):
    facts['virtual'] = True
    persona = 'SRX_BRANCH'
  else:
    raise RuntimeError("Unknown device persona: %s" % examine)
  
  facts['personality'] = persona
