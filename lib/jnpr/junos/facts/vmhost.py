from jnpr.junos.exception import RpcError
import re
from lxml import etree


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {
        "vmhost": "A boolean indicating if the device is vmhost.",
    }


def get_facts(device):
    """
    Gathers facts from the sysctl command.
    """
    SYSCTL_VMHOST_MODE = "sysctl -n hw.re.vmhost_mode"
    vmhost = None

    if device.facts["_is_linux"]:
        vmhost = False
    else:
        try:
            rsp = device.rpc.request_shell_execute(command=SYSCTL_VMHOST_MODE)
            if rsp.tag == "rpc-error":
                raise RpcError()
            result = re.sub("<[^<]+>", "", etree.tostring(rsp).decode())
            if result.strip() == "1":
                vmhost = True
            else:
                vmhost = False
        except RpcError:
            pass

    return {
        "vmhost": vmhost,
    }
