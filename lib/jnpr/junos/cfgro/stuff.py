from setup import *

dev = Device('jnpr-dc-fw').open()

srx = loadyaml('srx')

zones = srx['zoneTable'](dev)
zones.get()

pc = srx['policyContextTable'](dev)
pc.get()

addrs = srx['abitemTable'](dev)

rules = srx['policyRuleTable'](dev)
rules.get( policy=pc[0].name, namesonly=False )

