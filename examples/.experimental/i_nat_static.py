# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from exampleutils import *
from jnpr.eznc import Netconf as Junos
from jnpr.eznc.resources.srx.nat_static_simple import NatStaticSimple
from jnpr.eznc.utils import ConfigUtils

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)
jdev.open()

# meta-toolbox the config-utils package onto this object,
# this gives us access to: jdev.ez.cu.<functions>

jdev.ez( cu=ConfigUtils )     

# define a resource manager for simple source-NAT use-cases

rmgr = NatStaticSimple( jdev )

r_name = dict(ruleset_name="INBOUND_TRANSLATIONS", rule_name="WEB_Srvrs")
r = rmgr[r_name]

r_name = dict(ruleset_name="OUTBOUND_TRANSLATIONS", rule_name="WEB_Srvrs")
r = rmgr[r_name]
