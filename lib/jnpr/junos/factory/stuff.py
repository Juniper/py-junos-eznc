from setup import *

dev = Device('jnpr-dc-fw').open()

globals().update( loadyaml( '../op/ethport' ))
eths = EthPortTable(dev)

srx = loadyaml('srx')

zones = srx['zoneTable'](dev)
zones.get()

pctx = srx['policyContextTable'](dev)
pctx.get()

addrs = srx['abitemTable'](dev)
addrs.get(security_zone='OUTSIDE-DC-ST1')

rules = srx['policyRuleTable'](dev)
rules.get( policy=pctx[0].name, namesonly=False )

