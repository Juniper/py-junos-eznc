# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from jnpr.junos import Device 
from jnpr.junos.cfg.srx import ZoneAddrBook
from jnpr.junos.utils.config import Config

jdev = Device(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev.open()

# meta-toolbox the config-utils package onto this object,
# this gives us access to: jdev.ez.cu.<functions>

jdev.bind( cu=Config )     
jdev.bind( ab=ZoneAddrBook )

cu = jdev.cu
ab = jdev.ab

z_name = "OUTSIDE-DC-ST1"
zone = ab[z_name]

def test_addr():
  # grab the first address book entry, and change it's
  # ip_prefix to "1.1.1.1/32"

  first_addr = zone['$addrs'][0]
  addr = zone.addr[first_addr]
  addr(ip_prefix="1.1.1.1")
  addr.write()
  print cu.diff()
  cu.rollback()

def test_addr_set():
  # let's take a look at the address-set
  first_set = zone['$sets'][0]
  adr_set = zone.set[first_set]
  adr_set.propcopy('addr_list')
  adr_set['addr_list'].pop()
  adr_set.write()
  print cu.diff()
  cu.rollback()

test_addr()
test_addr_set()


