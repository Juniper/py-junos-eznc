import re

def personality( junos, facts ):
  
  model = facts['model']
  examine = model if model != 'Virtual Chassis' else facts['RE0']['model']
        
  if re.match("^(EX)|(QFX)", examine):
    persona = 'SWITCH'
  elif re.match("^MX", examine):
    persona = 'MX'
  elif re.match("^vMX", examine):
    facts['virtual'] = true
    persona = 'MX'
  elif re.match("SRX(\d){3}", examine):
    persona = 'SRX_BRANCH'
  elif re.match("firefly", examine, re.IGNORECASE):
    facts['virtual'] = True
    persona = 'SRX_BRANCH'
  elif re.match("SRX(\d){4}", examine):
    persona = 'SRX_HIGHEND'
  else:
    raise RuntimeError("Unknown device persona: %s" % examine)
  
  facts['personality'] = persona