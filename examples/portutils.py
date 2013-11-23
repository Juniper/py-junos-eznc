
from jnpr.junos.utils import Util

class PortUtils(Util):
  
  def get_macaddrs(self, glob=None, keymacaddr=True ):
    """
    Returns hash of macaddr:port-name

    :glob: (OPTIONAL)
      interface name glob for filtering search

    :keymacaddr: (OPTIONAL)
      determines the key/value of the return hash.  if 
      True, then macaddr is the key, otherwise the 
      port name is the key
    """
    args = {}
    args['media'] = True    # this will give us MACADDR information
    if glob is not None: args['interface_name'] = glob

    rsp = self.rpc.get_interface_information(**args)

    # find only those interfaces that have a link-level-type of
    # Ethernet, since we only care about MAC-addresses.  Need to 
    # use the normalize-space() XPATH function since Junos include 
    # newlines in the text output, phfft.

    eths = rsp.xpath('physical-interface[normalize-space(link-level-type)="Ethernet"]')

    def _m2n_():
      """ macaddr => port-name """
      return { 
        port.findtext('current-physical-address').strip() : port.findtext('name').strip() 
        for port in eths
      }

    def _n2m_():
      """ port-name => macaddr """
      return { 
        port.findtext('name').strip() : port.findtext('current-physical-address').strip()
        for port in eths
      }

    return _m2n_() if keymacaddr is True else _n2m_()

  def find_port_by_macaddr(self, macaddr, glob=None):
    """
    Return the physical interface name given :macaddr: or :None:
    if the :macaddr: is not found.

    :macaddr:
      the MAC-address to locate in the form: 'xx:xx:xx:xx:xx:xx'

    :glob: (OPTIONAL)
      an interface name glob-match, e.g. 'ge*', used to filter
      the search
    """
    macaddr_table = self.get_macaddrs(glob)
    return macaddr_table[macaddr] if macaddr in macaddr_table else None      

  def find_macaddr_by_ipaddr(self, ipaddr, glob=None):
    """
    Return the MAC-address of the physical port that is providing
    the requested :ipaddr: (by configuration).  If the :ipaddr:
    is not found, then return :None:

    :ipaddr:
      IPv4 address to look for, without the CIDR portion, e.g.
      '192.168.56.10'

    :glob: (OPTIONAL)
      The file-glob to filter the search, e.g. if you only
      want to search gigabit-ethernet ports, 'ge*'
    """
    # first retrieve a list of interfaces, basically doing the 
    # command 'show interfaces terse <ifmatch>'

    args = {}
    args['terse'] = True
    if glob is not None: args['interface_name'] = glob    
    rsp = self.rpc.get_interface_information(**args)

    # now find the ifa-local address that matches :ipaddr: and if it is
    # not found, then return None at this point.  The xpath() routine
    # always returns a list, even if it's empty (not-found). Here using
    # the XPATH starts-with() function since we don't want to deal with
    # handling the CIDR portion of the value (kinda cheating here)

    found = rsp.xpath('.//ifa-local[starts-with(normalize-space(.),"%s")]' % ipaddr)
    if 0 == len(found): return None

    # so we need to check the actual value against what we found, cuz we
    # cheated before in the XPATH lookup :-)  The actual value includes
    # the CIDR, so we need to only check the ipaddr part

    found_ipaddr = found[0].text.strip()
    if found_ipaddr.split('/')[0] != ipaddr: return None

    # now that we've got a match, let's grab the physical interface name.
    # again we can use XPATH for this purpose.  The found variable will
    # always be a list of 1 item, so we have to index it this way.

    if_name = found[0].xpath('ancestor::physical-interface/name')[0].text.strip()

    # now that we've got the physical interface name, we can retrieve the 
    # MAC address.

    rsp = self.rpc.get_interface_information(interface_name=if_name, media=True)
    return rsp.xpath('.//current-physical-address')[0].text.strip()

  def get_lldpnei_ipaddr(self, port):
    """
    Returns the LLDP neighbor management IP address for the given 
    physical port.

    :port:
      the name of the physical port, e.g. 'ge-0/0/0'
    """

    try:
      rsp = self.rpc.get_lldp_interface_neighbors_information(
        interface_name = port
      )
    except Exception:
      # basically means that the :port: value was invalid
      return "invalid port: %s" % port

    nei_mgmt = rsp.xpath('.//lldp-remote-management-address')
    nei_count = len(nei_mgmt)
    if not nei_count: return None
    if nei_count > 1: 
      #@@ this is not really an error, but just not handling this
      #@@ use-case at the moment
      return "There are %s neighbors on this port ..." % str(nei_count)

    return nei_mgmt[0].text.strip()








