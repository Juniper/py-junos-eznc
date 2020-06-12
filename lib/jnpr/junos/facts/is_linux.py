from jnpr.junos.exception import RpcError


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {
        "_is_linux": "A boolean indicating if the device is running linux" "kernel.",
    }


def get_facts(device):
    """
    Gathers the _is_linux fact using the <file-show/> RPC on the EVO version file.
    """

    # Temporary implementation until PR 1245634 is implemented.
    LINUX_VERSION_PATH = "/usr/share/cevo/cevo_version"

    is_linux = None

    try:
        rsp = device.rpc.file_show(normalize=True, filename=LINUX_VERSION_PATH)
        if rsp.tag == "file-content":
            is_linux = True
        else:
            is_linux = False
    except RpcError:
        is_linux = False
    return {
        "_is_linux": is_linux,
    }
