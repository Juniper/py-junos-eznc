import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from jnpr.junos import Device as Junos
from jnpr.junos.cfg.srx.nat import NatSrcPool, NatSrcRuleSet
from jnpr.junos.utils.config import Config

# create a junos device and open a connection

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev = Junos(**login)
jdev.open()

# now metabind some resource managers

jdev.bind( cu=Config )
jdev.bind( np=NatSrcPool )
jdev.bind( nr=NatSrcRuleSet )

# create a NAT source pool called 'POOL-A' with
# an address range from 198.18.0.1/32 to 198.18.0.10/32
# here showing the technique to change property values
# by making a "call" into the resource

r = jdev.np["POOL-A"]
r(addr_from="198.18.0.1", addr_to="198.18.0.10")
r.write()

# create a NAT source ruleset called "OUTBOUND_NAT"
# for a given zone-context matching on all traffic
# using HTTP (port-80), let's assume this is a compelely
# new ruleset, so we must set the zone-context
# here showing the technique to change property
#v values by accessing resource like a dictionary

rs = jdev.nr["OUTBOUND_NAT"]
rs['zone_from'] = 'JMET-DC-ST1'
rs['zone_to'] = 'OUTSIDE-DC-ST1'
rs.write()

# access the ruleset :rule: manager to setup 
# the specific rule, called "WWW".  since this
# object defaults the match addrs to 0/0, all
# we need to do is set the pool.

rule = rs.rule["WWW"]
rule(pool="POOL-A")
rule.write()

# now let's take a look at the config diff:

print jdev.cu.diff()
# [edit security]
# +   nat {
# +       source {
# +           pool POOL-A {
# +               address {
# +                   198.18.0.1/32 to 198.18.0.10/32;
# +               }
# +           }
# +           rule-set OUTBOUND_NAT {
# +               from zone JMET-DC-ST1;
# +               to zone OUTSIDE-DC-ST1;
# +               rule WWW {
# +                   match {
# +                       source-address 0.0.0.0/0;
# +                       destination-address 0.0.0.0/0;
# +                   }
# +                   then {
# +                       source-nat {
# +                           pool {
# +                               POOL-A;
# +                           }
# +                       }
# +                   }
# +               }
# +           }
# +       }
# +   }

print "rollback config to discard changes ..."
#jdev.cu.rollback()
