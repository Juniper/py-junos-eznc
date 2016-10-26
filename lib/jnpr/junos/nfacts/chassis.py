from jnpr.junos.exception import ConnectNotMasterError
from jnpr.junos.exception import RpcError

def provides_facts():
    return ('RE_hw_mi','model','serialnumber')

def get_facts(device):
    """
    """
    rsp = device.rpc.get_chassis_inventory()
    if rsp.tag == 'error':
        raise RpcError()

    if rsp.tag == 'output':
        # this means that there was an error; due to the
        # fact that this connection is not on the master
        # @@@ need to validate on VC-member
        raise ConnectNotMasterError()

    RE_hw_mi = False
    if rsp.tag == 'multi-routing-engine-results':
         RE_hw_mi = True

    model = rsp.findtext('.//chassis[1]/description')
    serialnumber = (
        rsp.findtext('.//chassis[1]/serial-number') or
        rsp.findtext('.//chassis-module[name="Backplane"]/serial-number') or
        rsp.findtext('.//chassis-module[name="Midplane"]/serial-number'))

    return {'RE_hw_mi': RE_hw_mi,
            'model': model,
            'serialnumber': serialnumber}