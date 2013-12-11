from setup import *

dev = Device('jnpr-dc-fw').open()

ETH = loadyaml( '../op/ethport' )
dev.bind(eths = ETH['EthPortTable'] )

SRX = loadyaml('../cfgro/srx')

zones = SRX['zoneTable'](dev)
zones.get()

pctx = SRX['policyContextTable'](dev)
pctx.get()

addrs = SRX['abitemTable'](dev)
addrs.get(security_zone='OUTSIDE-DC-ST1')

rules = SRX['policyRuleTable'](dev)
rules.get( policy=pctx[0].name, namesonly=False )

