# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from jnpr.junos import Device
from jnpr.junos.cfg.srx.nat import NatSrcPool
from jnpr.junos.utils.config import Config

jdev = Device(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev.open()

jdev.bind(cu=Config)
mgr = NatSrcPool(jdev)

def doit():
  make_pools = dict(
    this_pool =  dict(addr_from="1.1.1.1", addr_to="1.1.1.10"),
    that_pool =  dict(addr_from='2.2.2.2', addr_to="2.2.2.10"),
    goober_pool =  dict(addr_from="3.3.3.3", addr_to="3.3.3.10")
  )

  for pool_name, pool_vars in make_pools.items():
    print "creating pool name: %s" % pool_name
    r = mgr[pool_name]
    r(**pool_vars)
    r.write()

  print jdev.cu.diff()
# [edit security]
# +   nat {
# +       source {
# +           pool that_pool {
# +               address {
# +                   2.2.2.2/32 to 2.2.2.10/32;
# +               }
# +           }
# +           pool goober_pool {
# +               address {
# +                   3.3.3.3/32 to 3.3.3.10/32;
# +               }
# +           }
# +           pool this_pool {
# +               address {
# +                   1.1.1.1/32 to 1.1.1.10/32;
# +               }
# +           }
# +       }
# +   }
  
  print "rolling back..."
  jdev.cu.rollback()

doit()
