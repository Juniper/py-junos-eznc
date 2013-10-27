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

# Junos::Ez::Facts::Keeper.define( :routingengines ) do |ndev, facts|

#   re_facts = ['mastership-state','status','model','up-time','last-reboot-reason']
#   re_info = ndev.rpc.get_route_engine_information
#   re_info.xpath('//route-engine').each do |re|
#     slot_id = re.xpath('slot').text || "0"
#     slot = ("RE" + slot_id).to_sym
#     facts[slot] = Hash[ re_facts.collect{ |ele| [ ele.tr('-','_').to_sym, re.xpath(ele).text ] } ]
#     if facts[slot][:mastership_state].empty?
#       facts[slot].delete :mastership_state
#     else
#       facts[:master] = slot_id if facts[slot][:mastership_state] == 'master'
#     end
#   end
  
# end