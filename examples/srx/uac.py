class UAC(object):
  """
  SRX UAC helper utilities
  """
  def __init__(self,device):
    self.dev = device

  def get_users(self):
    """
    retrieves a list of UAC users, for each:
      username - user name 
      srcip - source IP
      rolename - role name
    """
    uac_table = self.dev.rpc.get_uac_auth_table(detail=True)
    self.users = [dict(srcip = entry.find('source').text,
          username = entry.find('username').text,
          rolename = entry.find('.//role-name').text)
      for entry in uac_table.xpath('entry') ]

  @property
  def user_names(self):
    """ returns a list of user-names """
    return [u['username'] for u in self.users]

  def find_uac_user(self, name):
    """ find a given user in the cache """
    def _match(x): return name == x['username'] # re.search(name, x['username'])
    return filter(_match, self.users)[0]

  def find_user_flows(self, ip_prefix):
    """ return a list of flow sessions based on the source ip_prefix """
    flows = self.dev.rpc.get_flow_session_information(source_prefix=ip_prefix)
    return [ flow.find('session-identifier').text.strip() 
      for flow in flows.xpath('flow-session')
    ]

  def get_user_flows(self, user_name ):
    """ return a list of session flows based on a user-name """
    user = self.find_uac_user( user_name )
    return self.find_user_flows( user['srcip'])

  def kill_user_flows(self, user_name):
    """ kill flow sessions based on a user-name """
    user = self.find_uac_user( user_name )
    self.dev.rpc.clear_flow_session(source_prefix=user['srcip'])