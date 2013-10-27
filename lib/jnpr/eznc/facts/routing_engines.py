from string import maketrans

def routing_engines(junos, facts):

  tr = maketrans('-','_')

  re_facts = ['mastership-state','status','model','up-time','last-reboot-reason']
  re_info = junos.rpc.get_route_engine_information()

  for re in re_info.xpath('.//route-engine'):
    x_slot = re.find('slot')
    slot_id = x_slot.text if x_slot is not None else "0"
    slot = "RE" + slot_id

    re_fd = {}
    facts[slot] = re_fd
    for factoid in re_facts:
      x_f = re.find(factoid)
      if x_f is not None:
        re_fd[factoid.translate(tr)] = x_f.text

    if re_fd.has_key('mastership_state'):
      if facts[slot]['mastership_state'] == 'master':
        facts['master'] = slot_id 
