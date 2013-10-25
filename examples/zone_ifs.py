# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from exampleutils import *
from jnpr.eznc import Netconf as Junos
from jnpr.eznc.resources.srx import Zone
from jnpr.eznc.utils import ConfigUtils

login = dict(user='jeremy', host='vsrx_cyan', password="jeremy1")

jdev = Junos(**login)
jdev.open()

# meta-toolbox the config-utils package onto this object,
# this gives us access to: jdev.ez.cu.<functions>

jdev.ez( cu=ConfigUtils ) 
jdev.ez( zone=Zone )    

cu = jdev.ez.cu

z_name = jdev.ez.zone.list[0]
zone = jdev.ez.zone[z_name]

first_ifs = zone.ifs.list[0]
ifs = zone.ifs[first_ifs]


