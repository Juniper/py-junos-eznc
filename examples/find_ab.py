# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from exampleutils import *
from jnpr.eznc import Netconf as Junos
from jnpr.eznc.resources.srx import Zone, ZoneAddrFinder
from jnpr.eznc.utils import ConfigUtils

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)
jdev.open()

# meta-toolbox the config-utils package onto this object,
# this gives us access to: jdev.ez.cu.<functions>

jdev.ez( cu=ConfigUtils )     
jdev.ez( zone=Zone )

cu = jdev.ez.cu
zone_mgr = jdev.ez.zone

z_name = zone_mgr.list[0]
zone = zone_mgr[z_name]

print "Reading zone address book ..."
zone.ab.read()

find_addr = "23.170.40.80"
print "Searching for address: " + find_addr
f = ZoneAddrFinder(zone)
r = f.find(find_addr)

print "\nAll items:"
pp(r.items)
# ['NET-23.170.40.0/24',
#  'NET-23.170.40.80/29',
#  'GCS-ST1-FOOSET-KOFAX',
#  'DEFAULT-PROTECT-NETS',
#  'DEFAULT-PROTECT-WINDOWS']

print "\nJust matching address items:"
pp(r.addrs)
# ['NET-23.170.40.0/24', 'NET-23.170.40.80/29']

print "\nJust matching address sets:"
pp(r.sets)
# ['GCS-ST1-FOOSET-KOFAX',
#  'DEFAULT-PROTECT-NETS',
#  'DEFAULT-PROTECT-WINDOWS']






