# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from exampleutils import *
from jnpr.eznc import Netconf as Junos
from jnpr.eznc.resources.srx import ZoneAddrBook
from jnpr.eznc.utils import ConfigUtils

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)
jdev.open()

# meta-toolbox the config-utils package onto this object,
# this gives us access to: jdev.ez.cu.<functions>

jdev.ez( cu=ConfigUtils )     
jdev.ez( ab=ZoneAddrBook )

cu = jdev.ez.cu
ab = jdev.ez.ab

z_name = "OUTSIDE-DC-ST1"
zone = jdev.ez.ab[z_name]

# grab the first address book entry, and change it's
# ip_prefix to "1.1.1.1/32"

first_addr = zone['$addrs'][0]
addr = zone.addr[first_addr]
addr(ip_prefix="1.1.1.1")
addr.write()

print cu.diff()
cu.rollback()

