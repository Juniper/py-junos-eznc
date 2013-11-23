import pdb

from itertools import groupby

class UAC(object):
  """
  SRX UAC helper utilities
  """
  def __init__(self,device):
    self.dev = device

  def get_users(self):
    """
    retrieves a list of UAC users, for each:
      name - user name 
      ipaddr - source IP
      role - role name
    """
    uac_table = self.dev.rpc.get_uac_auth_table(detail=True)
    self.users = [dict(ipaddr = entry.find('source').text,
          name = entry.find('username').text,
          role = entry.find('.//role-name').text)
      for entry in uac_table.xpath('entry') ]

  @property
  def usernames(self):
    """ returns a list of user-names """
    return [u['name'] for u in self.users]

  def user(self, name):
    """ find a given user in the cache """
    def _match(x): return name == x['name'] # re.search(name, x['username'])
    return filter(_match, self.users)[0]

  def _flows_by_srcprefix(self,ip_prefix):
    return self.dev.rpc.get_flow_session_information(source_prefix=ip_prefix)

  def _flowids_bysrcip(self, ip_prefix):
    """ return a list of flow sessions based on the source ip_prefix """
    flows = self._flows_by_srcprefix(ip_prefix)
    return [ flow.find('session-identifier').text.strip() 
      for flow in flows.xpath('flow-session') ]

  def user_flowids(self, user_name ):
    """ return a list of session flow IDs based on a user-name """
    user = self.user( user_name )
    return self._flowids_bysrcip( user['ipaddr'])

  def user_byteusage( self, user_name ):
    user = self.user( user_name )
    flows = self._flows_by_srcprefix(user['ipaddr'])
    sflows = sorted(flows.xpath('.//flow-information'),key=lambda x:x.find('direction').text.strip())
    sums = {}
    for fdir,gdata in groupby(sflows, lambda x: x.find('direction').text.strip()):
      sums[fdir] = sum([int(f.find('byte-cnt').text) for f in gdata])
    sums['total'] = sum(sums.values())
    return sums

  def kill_user_flows(self, user_name):
    """ kill flow sessions based on a user-name """
    user = self.user( user_name )
    self.dev.rpc.clear_flow_session(source_prefix=user['ipaddr'])
