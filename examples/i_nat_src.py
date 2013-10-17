# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from exampleutils import *
from jnpr.eznc import Netconf as Junos
from jnpr.eznc.resources.srx.nat_src_simple import NatSourceSimple
from jnpr.eznc.utils import ConfigUtils

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')

jdev = Junos(**login)
jdev.open()

# meta-toolbox the config-utils package onto this object,
# this gives us access to: jdev.ez.cu.<functions>

jdev.ez( cu=ConfigUtils )     

# define a resource manager for simple source-NAT use-cases

rmgr = NatSourceSimple( jdev )

defaults = dict(
  zone_from='OUTSIDE-DC-ST1',
  zone_to='PII-SOX-DC-ST1' )

def load_defaults(r):
 for k,v in defaults.items(): r[k]=v

def make_simple():
  r = rmgr["outbound-all"]
  load_defaults(r)
  r['pool_from_addr'] = '198.18.0.1'
  r['pool_to_addr'] = '198.18.0.10'
  r.write()
  return r

def make_specific():

  specific = dict(
    ruleset_name='outbound-all', 
    rule_name='more_specific', 
    pool_name='just_10_192')

  r = rmgr[ specific ]

  load_defaults(r)

  r['match_src_addr'] = '10.192.0.0/16'
  r['pool_from_addr'] = '200.18.0.1'
  r['pool_to_addr'] = '208.18.0.20'

  r.write()
  return r
