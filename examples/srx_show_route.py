# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from exampleutils import *
from jnpr.eznc import Netconf as Junos
from jnpr.eznc.utils import ConfigUtils

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev = Junos(**login)
jdev.open()

def show_sroute(jdev, *vargs, **kvargs):

  route = kvargs.get('route') or vargs[0][0]

  # do a 'show route' to determine the next-hop interface
  # if the route is unknown, then return found=False

  rsp = jdev.rpc.get_route_information(destination=route, best=True)
  nh_via = rsp.xpath('.//nh/nh-local-interface | .//nh/via')
  if not len(nh_via):
    return {'found': False}

  # now take the next-hop interface text value and
  # feed that into a show interface to obtain the
  # security zone

  nh_via = nh_via[0]
  nh_ifs = nh_via.text
  nh_proto = nh_via.xpath('ancestor::rt-entry/protocol-name')[0].text
  dest = nh_via.xpath('ancestor::rt/rt-destination')[0].text
  rsp = jdev.rpc.get_interface_information(interface_name=nh_ifs)
  zone = rsp.find('.//logical-interface-zone-name')
  if zone is None:
    return {'found': False}

  got = { 'found': True,
    'destination': dest,
    'interface': nh_ifs,
    'protocol': nh_proto,
    'zone': zone.text.strip()
  }

  return got

jdev.ez(sroute=show_sroute)
