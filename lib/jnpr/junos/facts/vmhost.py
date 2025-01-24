from jnpr.junos.exception import RpcError
import re
from lxml import etree

def _get_vmhost_version_information(device):
    multi_re = False
    try:
        rsp = device.rpc.get_route_engine_information(normalize=True)
        re_list = rsp.findall(".//route-engine")
        if len(re_list) > 1:
            multi_re = True
        else:
            multi_re = False
    except RpcError as err:
        pass

    if multi_re == True:
        try:
            return device.rpc.cli(
                "show vmhost version invoke-on all-routing-engines", format="xml", normalize=True
            )
        except RpcError as err:
            raise RpcError()
    else:
        try:
            return device.rpc.cli(
                "show vmhost version", format="xml", normalize=True
            )
        except RpcError as err:
            raise RpcError()

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
    vmhost_info = {}
    vm_ver_rsp = None

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

    if vmhost == True:
        rsp = _get_vmhost_version_information(device)
        if rsp.tag == "output":
            pass
        else:
            if rsp.tag == "vmhost-version-information":
                vm_ver_rsp = [rsp]
            else:
                vm_ver_rsp = rsp.findall(".//vmhost-version-information")
            vmhost_info = {}

            for re_vm_ver_info in vm_ver_rsp:
                re_name = re_vm_ver_info.findtext("../re-name", "re0")
                vmhost_current_root_set = re_vm_ver_info.findtext("./current-root-set")
                vmhost_set_junos_version_set_p = re_vm_ver_info.findtext("./set-disk-info[set-disk-name = 'set p']/set-junos-version")
                vmhost_set_junos_version_set_b = re_vm_ver_info.findtext("./set-disk-info[set-disk-name = 'set b']/set-junos-version")

                vmhost_info[re_name] = {
                    "vmhost_current_root_set": vmhost_current_root_set,
                    "vmhost_version_set_p" : vmhost_set_junos_version_set_p,
                    "vmhost_version_set_b": vmhost_set_junos_version_set_b,
               }

    return {
        "vmhost": vmhost,
        "vmhost_info": vmhost_info,
    }
