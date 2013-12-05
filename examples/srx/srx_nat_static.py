import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from jnpr.junos import Device as Junos
from jnpr.junos.cfg.srx.nat import NatStaticRuleSet
from jnpr.junos.utils.config import Config

# create a junos device and open a connection

jdev = Junos(user='jeremy', password='jeremy1', host='vsrx_cyan')
jdev.open()

# now metabind some resource managers

jdev.bind( cu=Config )
jdev.bind( nat=NatStaticRuleSet )

# create a static NAT ruleset called 'outside' and map it on the from-zone "OUTSIDE-DC-STD1"

nat = jdev.nat["outside"]
nat(zone_from="OUTSIDE-DC-ST1")
nat.write()

# now create a rule within that ruleset called "foo" to static NAT 198.18.11.5 to 10.0.0.4
# for port 80.  Also enable proxy-arp on interface reth0.213"

r = nat.rule["foo"]
r(match_dst_addr="198.18.11.5", match_dst_port="80", nat_addr="10.0.0.4", nat_port="80")
r(proxy_interface="reth0.213")
r.write()

print jdev.cu.diff()

# [edit security]
# +   nat {
# +       static {
# +           rule-set outside {
# +               from zone OUTSIDE-DC-ST1;
# +               rule foo {
# +                   match {
# +                       destination-address 198.18.11.5/32;
# +                       destination-port 80;
# +                   }
# +                   then {
# +                       static-nat {
# +                           prefix {
# +                               10.0.0.4/32;
# +                               mapped-port 80;
# +                           }
# +                       }
# +                   }
# +               }
# +           }
# +       }
# +       proxy-arp {
# +           interface reth0.213 {
# +               address {
# +                   198.18.11.5/32;
# +               }
# +           }
# +       }
# +   }

print "rollback config ..."
jdev.cu.rollback()


