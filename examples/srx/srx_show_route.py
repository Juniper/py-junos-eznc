# for debugging ...
import pdb
from pprint import pprint as pp 
from lxml import etree

# for the example ...
from jnpr.junos import Device as Junos

login = dict(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev = Junos(**login)
jdev.open()

def show_sroute(jdev, *vargs, **kvargs):
  """
  given a route destination, provide a dictionary of information 
  about that route that includes the interface and security-zone

  kvargs['route'] or vargs[0]
    the route to lookup
  """

  route = kvargs.get('route') or vargs[0]

  # do a 'show route' to determine the next-hop interface
  # if the route is unknown, then return found=False

  rsp = jdev.rpc.get_route_information(destination=route, best=True)
  nh_via = rsp.xpath('.//nh/nh-local-interface | .//nh/via')
  if not len(nh_via):
    return {'found': False}

  # now take the next-hop interface text value and
  # feed that into a show interface to obtain the
  # security zone

  nh_via = nh_via[0] # first child
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

jdev.bind(show_sroute)

print "now call jdev.show_sroute(...) with the route you want to find"

# >>> jdev.show_sroute("23.171.140.0/24")
# {'interface': 'ge-0/0/1.371', 'found': True, 
#  'destination': '23.171.140.0/22', 'protocol': 'Direct', 'zone': 'DEFAULT-PROTECT-DC-ST1'}
#
# --or--
#
# >>> jdev.show_sroute(route="23.171.140.0/24")
# {'interface': 'ge-0/0/1.371', 'found': True, 
#  'destination': '23.171.140.0/22', 'protocol': 'Direct', 'zone': 'DEFAULT-PROTECT-DC-ST1'}
