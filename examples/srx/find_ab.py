# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

import sys

# for the example ...
from jnpr.eznc import Netconf as Junos
from jnpr.eznc.resources.srx import Zone, ZoneAddrFinder

def die(msg):
  print "-" * 50
  print "DIE!: " + msg
  print "-" * 50
  exit(1)

try:  
  find_addr = sys.argv[1]
except:
 die("You must specify the ip-addr to locate")


jdev = Junos(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev.open()

# meta-toolbox the config-utils package onto this object,
# this gives us access to: jdev.ez.cu.<functions>

jdev.bind( zone=Zone )

zone_mgr = jdev.zone

z_name = zone_mgr.list[0]
zone = zone_mgr[z_name]

print "Reading zone %s address book ..." % z_name
zone.ab.read()

def do_find_addr( find_addr ):
  print "Searching for address: " + find_addr
  f = ZoneAddrFinder(zone)
  r = f.find(find_addr)

  print "\nAll items:"
  pp(r.items)

  print "\nJust matching address items:"
  pp(r.addrs)

  print "\nLongest-Prefix-Match:"
  pp(r.lpm)

  print "\nJust matching address sets:"
  pp(r.sets)

do_find_addr( find_addr )