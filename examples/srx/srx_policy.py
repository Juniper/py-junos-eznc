# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.cfg.srx import PolicyContext

jdev = Device(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev.open()

# meta-toolbox the config-utils package onto this object,
# this gives us access to: jdev.ez.cu.<functions>

jdev.bind( cu=Config )   

# now add the PolicyContext, this will auto-load the associated
# rules resource class PolicyRule

jdev.bind( pc=PolicyContext )

# now access a policy PolicyContext.  The policy context is
# tuple (from-zone-name, to-zone-name)

r = jdev.pc[("OUTSIDE-DC-ST1","PII-SOX-DC-ST1")]

# dump the contents:
pp(r)
# NAME: PolicyContext: ('OUTSIDE-DC-ST1', 'PII-SOX-DC-ST1')
# HAS: {'_active': True,
#  '_exists': True,
#  'rules': ['100',
#            '103',
#            '105',
#            '110',
# <...snipped for size...>
#            '650',
#            '655',
#            '660',
#            '665',
#            '670',
#            '675',
#            'DENY-DC-OUTSIDE-DC-ST1-TO-PII-SOX-DC-ST1-TCP',
#            'DENY-DC-OUTSIDE-DC-ST1-TO-PII-SOX-DC-ST1',
#            'DENY-OUTSIDE-DC-ST1-TO-PII-SOX-DC-ST1-TCP',
#            'DENY-OUTSIDE-DC-ST1-TO-PII-SOX-DC-ST1'],
#  'rules_count': 86}
# SHOULD:{}

# now access a specific rule in this context

rule = r.rule["655"]

# and dump that.

# pp(rule)
# NAME: PolicyRule: 655
# HAS: {'_active': True,
#  '_exists': True,
#  'action': 'permit',
#  'match_apps': ['TCP-3281'],
#  'match_dsts': ['HOST-SUGARGATE.CORP', 'HOST-TAKKA.CORP', 'HOST-ULTROS.CORP'],
#  'match_srcs': ['JNPR-VPN-USER-SUBS',
#                 'RTINO-VP2-DESKTOP-NETS',
#                 'RTINO-RC3-DESKTOP-NETS',
#                 'OFFSHORE-DC-ACCESS']}
# SHOULD:{}

# we can modify the contents, like adding a few new apps.  we 
# copy what is there first, and then add to it

rule.propcopy('match_apps')
rule['match_apps'].append( "TCP-21")
rule['match_apps'].append(" TCP-99")

# write the rule back to the device
rule.write()

# display the changes:
print jdev.cu.diff()

# [edit security policies from-zone OUTSIDE-DC-ST1 to-zone PII-SOX-DC-ST1 policy 655 match]
# -      application TCP-3389;
# +      application [ TCP-3389 TCP-99 TCP-21 ];

# you can do things like reorder rules, for example:

rule.reorder(before="105")

# and see the change:

print jdev.cu.diff()
# [edit security policies from-zone OUTSIDE-DC-ST1 to-zone PII-SOX-DC-ST1]
#      policy 103 { ... }
# !     policy 655 { ... }

# now discard these changes

print "Rolling back ..."
jdev.cu.rollback()

