from setup import *

dev = Device('jnpr-dc-fw').open()
data = loader.load('test')
pc = Table(dev,data['CfgSecPolicyContextTable'])
pc.get()
this = pc.keys()[0]

pr = Table(dev,data['CfgSecPolicyRuleTable'])
phys = Table(dev,data['CfgPhyPortTable'])
ab = Table(dev,data['CfgZoneAddrBookItemTable'])
