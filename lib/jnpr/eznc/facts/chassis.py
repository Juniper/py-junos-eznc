from lxml.builder import E

def chassis(junos, facts):
  """
  """
  rsp = junos.rpc.get_chassis_inventory()
  x_ch = rsp.find('chassis')

  facts['hardwaremodel'] = x_ch.find('description').text
  facts['serialnumber'] = x_ch.find('serial-number').text

  got = junos.rpc.get_config(
    E.system(
      E('host-name'),
      E('domain-name')
    )
  )

  hostname = got.find('.//host-name')
  if hostname is not None: facts['hostname'] = hostname.text
  facts['fqdn'] = facts['hostname']

  domain = got.find('.//domain-name')
  if domain is not None: 
    facts['domain'] = domain.text
    facts['fqdn'] += '.%s' % facts['domain']    

