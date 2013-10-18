# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from exampleutils import *
from jnpr.eznc import Netconf as Junos
from jnpr.eznc.resources.srx.nat import NatSrcRuleSet
from jnpr.eznc.utils import ConfigUtils

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)
jdev.open()

jdev.ez(cu=ConfigUtils)
mgr = NatSrcRuleSet(jdev)

rs = mgr["Goober"]
r = rs.rule["G_WWW"]


