# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from jnpr.junos import Device
from jnpr.junos.cfg.srx import Zone
from jnpr.junos.utils.config import Config

jdev = Device(user='jeremy', host='vsrx_cyan', password="jeremy1")
jdev.open()

# meta-toolbox the config-utils package onto this object,
# this gives us access to: jdev.ez.cu.<functions>

jdev.bind( cu=Config ) 
jdev.bind( zone=Zone )    

cu = jdev.cu

z_name = jdev.zone.list[0]
zone = jdev.zone[z_name]

first_ifs = zone.ifs.list[0]
ifs = zone.ifs[first_ifs]


