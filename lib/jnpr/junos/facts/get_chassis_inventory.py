from jnpr.junos.exception import ConnectNotMasterError
from jnpr.junos.exception import RpcError

def provides_facts():
    return ('RE_hw_mi','serialnumber',)

def get_facts(device):
    """
    """
    rsp = device.rpc.get_chassis_inventory()
    if rsp.tag == 'error':
        raise RpcError()

    if (rsp.tag == 'output' and
        rsp.text.find('can only be used on the master routing engine') != -1):
        # An error; due to the fact that this RPC can only be executed on the
        # master Routing Engine
        raise ConnectNotMasterError()

    RE_hw_mi = False
    if rsp.tag == 'multi-routing-engine-results':
         RE_hw_mi = True

    serialnumber = (
        rsp.findtext('.//chassis[1]/serial-number') or
        rsp.findtext('.//chassis-module[name="Backplane"]/serial-number') or
        rsp.findtext('.//chassis-module[name="Midplane"]/serial-number'))

    return {'RE_hw_mi': RE_hw_mi,
            'serialnumber': serialnumber,}