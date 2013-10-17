# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from exampleutils import *
from jnpr.eznc import Netconf as Junos
from jnpr.eznc.resources.srx.nat_src_simple import NatSourceSimple
from jnpr.eznc.utils import ConfigUtils

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)
jdev.open()

# meta-toolbox the config-utils package onto this object,
# this gives us access to: jdev.ez.cu.<functions>

jdev.ez( cu=ConfigUtils )     

# define a resource manager for simple source-NAT use-cases

rmgr = NatSourceSimple( jdev )

# if you want to see the resource properties, you could do:
# >>> print NatSourceSimple.PROPERTIES
# ['zone_from', 'zone_to', 'match_src_addr', 'match_dst_addr', 'pool_from_addr', 'pool_to_addr']

# define some default properties we'll use:

##### -------------------------------------------------------------------------
##### now create a super-simple config that all uses the same name "oubound-all"
##### name for the rule-set name, the rule name, and the pool name
##### -------------------------------------------------------------------------

def create_general():
  # access the resource with the name

  r = rmgr["outbound-all"]

  # set properties; the pool address range.  
  r['zone_from'] = 'OUTSIDE-DC-ST1'
  r['zone_to'] = 'PII-SOX-DC-ST1'
  r['pool_from_addr'] = '198.18.0.1'
  r['pool_to_addr'] = '198.18.0.10'

  # use the default values for everything else ...
  # the match source/address defaults to '0.0.0.0/32'

  # now write the config to the device, this does not commit, just loads the changes ..

  r.write()
  return r

r = create_general()

# now display the diff (show|compare)
print jdev.ez.cu.diff()

# [edit security]
# +   nat {
# +       source {
# +           pool outbound-all {
# +               address {
# +                   198.18.0.1/32 to 198.18.0.10/32;
# +               }
# +           }
# +           rule-set outbound-all {
# +               from zone OUTSIDE-DC-ST1;
# +               to zone PII-SOX-DC-ST1;
# +               rule outbound-all {
# +                   match {
# +                       source-address 0.0.0.0/0;
# +                       destination-address 0.0.0.0/0;
# +                   }
# +                   then {
# +                       source-nat {
# +                           pool {
# +                               outbound-all;
# +                           }
# +                       }
# +                   }
# +               }
# +           }
# +       }
# +   }


##### -------------------------------------------------------------------------
##### create a more specific example.  we'll use the same rule-set, but a 
##### different rule name and pool name
##### -------------------------------------------------------------------------

def create_specific():
  # create a name with specific properties:

  specific_name = dict(
    ruleset_name='my_ruleset-all', 
    rule_name='more_specific', 
    pool_name='just_10_192')

  # set up a resource object from the manager

  r = rmgr[ specific_name ]

  # now set the properties we want to write ...

  r['zone_from'] = 'PCI-APP-DC-ST1'
  r['zone_to'] = 'OUTSIDE-DC-ST1'
  r['match_src_addr'] = '10.192.0.0/16'
  r['pool_from_addr'] = '200.18.0.1'
  r['pool_to_addr'] = '208.18.0.20'

  # and store them to the device
  r.write()
  return r

r = create_specific()

# show all the differences thus far ... we haven't committed anything, so
# we'll see the prior example here too.
print jdev.ez.cu.diff()

# [edit security]
# +   nat {
# +       source {
# +           pool outbound-all {
# +               address {
# +                   198.18.0.1/32 to 198.18.0.10/32;
# +               }
# +           }
# +           pool just_10_192 {
# +               address {
# +                   200.18.0.1/32 to 208.18.0.20/32;
# +               }
# +           }
# +           rule-set outbound-all {
# +               from zone OUTSIDE-DC-ST1;
# +               to zone PII-SOX-DC-ST1;
# +               rule outbound-all {
# +                   match {
# +                       source-address 0.0.0.0/0;
# +                       destination-address 0.0.0.0/0;
# +                   }
# +                   then {
# +                       source-nat {
# +                           pool {
# +                               outbound-all;
# +                           }
# +                       }
# +                   }
# +               }
# +           }
# +           rule-set my_ruleset-all {
# +               from zone PCI-APP-DC-ST1;
# +               to zone OUTSIDE-DC-ST1;
# +               rule more_specific {
# +                   match {
# +                       source-address 10.192.0.0/16;
# +                       destination-address 0.0.0.0/0;
# +                   }
# +                   then {
# +                       source-nat {
# +                           pool {
# +                               just_10_192;
# +                           }
# +                       }
# +                   }
# +               }
# +           }
# +       }
# +   }

# if you want to commit these changes you could do:
#dev.ez.cu.commit_check()
#jdev.ez.cu.commit()

# or if you want to discard the changes:
#print "Rollback now ..."
#jdev.ez.cu.rollback()