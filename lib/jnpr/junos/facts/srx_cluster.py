"""
facts['srx_cluster'] = True | False
  if personality.startswith('SRX')
  device responds to the "show" command to extract the data

Facts Required:
  personality
"""


def facts_srx_cluster(junos, facts):
    if not facts['personality'].startswith('SRX'):
        return

    # we should check the 'cluster status' on redundancy group 0 to see who is
    # master.  we use a try/except block for cases when SRX is not clustered

    try:
        cluster_st = junos.rpc.get_chassis_cluster_status(redundancy_group="0")
        primary = cluster_st.xpath(
            './/redundancy-group-status[.="primary"]')[0]
        node = primary.xpath(
            'preceding-sibling::device-name[1]')[0].text.replace('node', 'RE')
        if not facts.get('master'):
            facts['master'] = node
        elif node not in facts['master']:
            facts['master'].append(node)
        facts['srx_cluster'] = True
    except:
        facts['srx_cluster'] = False
        pass
