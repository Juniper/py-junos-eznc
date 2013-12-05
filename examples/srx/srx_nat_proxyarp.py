# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from jnpr.junos import Device
from jnpr.junos.cfg.srx.nat import NatProxyArp
from jnpr.junos.utils.config import Config

# create a junos device and open a connection

jdev = Device(user='jeremy', password='jeremy1', host='vsrx_cyan')
jdev.open()

# create a config utility object
cu = Config(jdev)

# select a proxy-arp entry, using direct resource access
entry = NatProxyArp(jdev, ('ge-0/0/1.124', '198.18.11.5'))

def doit():
  if not entry.exists:
    print "creating entry"
    entry.write(touch=True)
    print cu.diff()
# [edit security]
# +   nat {
# +       proxy-arp {
# +           interface ge-0/0/1.124 {
# +               address {
# +                   198.18.11.5/32;
# +               }
# +           }
# +       }
# +   }
    print "rollback...."
    cu.rollback()
  else:
    print "entry exists"

doit()  
