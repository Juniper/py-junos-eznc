from jnpr.junos.exception import RpcError


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'is_evo': "A boolean indicating if the device is running EVO "
                      "software.", }


def get_facts(device):
    """
    Gathers the is_evo fact using the <file-show/> RPC on the EVO version file.
    """

    # Temporary implementation until PR 1245634 is implemented.
    EVO_VERSION_PATH = '/usr/share/cevo/cevo_version'

    is_evo = None

    try:
        rsp = device.rpc.file_show(normalize=True, filename=EVO_VERSION_PATH)
        if rsp.tag == 'file-content':
            is_evo = True
        else:
            is_evo = False
    except RpcError:
        is_evo = False
    return {'is_evo': is_evo, }
