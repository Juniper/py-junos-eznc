import pdb
import re

def software_version(junos, facts):
  
  f_persona = facts.get('personality')
  f_master = facts.get('master')
      
  if f_persona == 'MX':
    x_swver = junos.cli("show version invoke-on all-routing-engines", format='xml')

  elif f_persona == 'SWITCH':
    ## most EX switches support the virtual-chassis feature, so the 'all-members' option would be valid
    ## in some products, this options is not valid (i.e. not vc-capable. so we're going to try for vc, and if that
    ## throws an exception we'll rever to non-VC
    try:
      x_swver = junos.rpc.cli("show version all-members", format='xml')
    except:
      facts['vc_capable'] = False
      x_swver = junos.rpc.cli("show version", format='xml')
    else:
      facts['vc_capable'] = True
  else:
    x_swver = junos.rpc.cli("show version",format='xml')
  
  if x_swver[0].tag == 'multi-routing-engine-results':
    raise RuntimeError("Multi-RE platform found -- IMPLEMENT ME!")
    # swver_infos = swver.xpath('//software-information')
    # swver_infos.each do |re_sw|
    #   re_name = re_sw.xpath('preceding-sibling::re-name').text.upcase
    #   re_sw.xpath('package-information[1]/comment').text =~ /\[(.*)\]/
    #   ver_key = ('version_' + re_name).to_sym
    #   facts[ver_key] = $1
    # end
    # master_id = f_master
    # facts[:version] =
    #   facts[("version_" + "RE" + master_id).to_sym] ||
    #   facts[('version_' + "FPC" + master_id).to_sym]
  else:
    pkginfo = x_swver.xpath('.//package-information[name = "junos"]/comment')[0].text    
    facts['version'] = re.findall(r'\[(.*)\]', pkginfo)[0]
