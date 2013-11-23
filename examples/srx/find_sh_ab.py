# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

import sys

# for the example ...
from jnpr.junos import Device as Junos
from jnpr.junos.cfg.srx import SharedAddrBook, AddrBookFinder

def die(msg):
  print "-" * 50
  print "DIE!: " + msg
  print "-" * 50
  exit(1)

def show_help():
  print "%s <ab_name> <ip_addr>" % sys.argv[0]
  exit(1)

if len(sys.argv) != 3:
  show_help()

try:  
  book_name = sys.argv[1]
  find_addr = sys.argv[2]
except:
 die("You must specify the ip-addr to locate")


jdev = Junos(user='jeremy', host='vsrx_x46', password='jeremy1')
jdev.open()

# meta-toolbox the config-utils package onto this object,
# this gives us access to: jdev.ez.cu.<functions>

jdev.bind( ab=SharedAddrBook )

book = jdev.ab[book_name]
if not book.exists:
  die("Book %s does not exist on this device!" % book_name )

def do_find_addr( find_addr ):
  print "Searching for address: " + find_addr
  f = AddrBookFinder(book)
  r = f.find(find_addr)

  print "\nAll items:"
  pp(r.items)

  print "\nJust matching address items:"
  pp(r.addrs)

  print "\nLongest-Prefix-Match:"
  pp(r.lpm)

  print "\nJust matching address sets:"
  pp(r.sets)
  return r

results = do_find_addr( find_addr )
