def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {
        "HOME": "A string indicating the home directory of the current " "user.",
    }


def get_facts(device):
    """
    Gathers facts from the <file-list/> RPC.
    """
    home = None
    rsp = device.rpc.file_list(normalize=True, path="~")
    if rsp.tag == "directory-list":
        dir_list_element = rsp
    else:
        dir_list_element = rsp.find(".//directory-list")
    if dir_list_element is not None:
        home = dir_list_element.get("root-path")
        if home is not None:
            home = home.rstrip("/")
    return {
        "HOME": home,
    }
