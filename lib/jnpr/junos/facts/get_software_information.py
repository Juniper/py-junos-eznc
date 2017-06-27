import re
from jnpr.junos.facts.swver import version_info
from jnpr.junos.exception import RpcError


def _get_software_information(device):
    # See if device understands "invoke-on all-routing-engines"
    try:
        return device.rpc.cli("show version invoke-on all-routing-engines",
                              format='xml', normalize=True)
    except RpcError:
        # See if device is VC Capable
        if device.facts['vc_capable'] is True:
            try:
                return device.rpc.cli("show version all-members", format='xml',
                                      normalize=True)
            except Exception:
                pass
        try:
            sw_info = device.rpc.get_software_information(normalize=True)
            if sw_info is True:
                # Possibly an NFX which requires 'local' and 'detail' args.
                sw_info = device.rpc.get_software_information(local=True,
                                                              detail=True,
                                                              normalize=True)
            return sw_info
        except Exception:
            pass


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'junos_info': "A two-level dictionary providing Junos software "
                          "version information for each RE in the system. "
                          "The first-level key is the name of the RE. The "
                          "second level key is 'text' for the version as a "
                          "string and 'object' for the version as a "
                          "version_info object.",
            'hostname': 'A string containing the hostname of the current '
                        'Routing Engine.',
            'hostname_info': 'A dictionary keyed on Routing Engine name. The '
                             'value of each key is the hostname of the '
                             'Routing Engine.',
            'model': 'An uppercase string containing the model of the chassis '
                     'in which the current Routing Engine resides.',
            'model_info': 'A dictionary keyed on Routing Engine name. The '
                          'value of each key is an uppercase string '
                          'containing the model of the chassis in which the '
                          'Routing Engine resides.',
            'version': 'A string containing the Junos version of the current '
                       'Routing Engine.',
            'version_info': 'The Junos version of the current Routing Engine '
                            'as a version_info object.',
            'version_RE0': "A string containing the Junos version of the "
                           "RE in slot 0. (Assuming the system contains an "
                           "RE0.)",
            'version_RE1': "A string containing the Junos version of the "
                           "RE in slot 1. (Assuming the system contains an "
                           "RE1)", }


def get_facts(device):
    """
    Gathers facts from the <get-software-information/> RPC.
    """
    junos_info = None
    hostname = None
    hostname_info = None
    model = None
    model_info = None
    version = None
    ver_info = None
    version_RE0 = None
    version_RE1 = None

    rsp = _get_software_information(device)

    si_rsp = None
    if rsp.tag == 'software-information':
        si_rsp = [rsp]
    else:
        si_rsp = rsp.findall('.//software-information')

    for re_sw_info in si_rsp:
        re_name = re_sw_info.findtext('../re-name', 're0')
        re_model = re_sw_info.findtext('./product-model')
        re_hostname = re_sw_info.findtext('./host-name')
        # First try the <junos-version> tag present in >= 15.1
        re_version = re_sw_info.findtext('./junos-version')
        if re_version is None:
            # For < 15.1, get version from the "junos" package.
            try:
                re_pkg_info = re_sw_info.findtext(
                    './package-information[name="junos"]/comment'
                )
                if re_pkg_info is not None:
                    re_version = re.findall(r'\[(.*)\]', re_pkg_info)[0]
                else:
                    # NFX JDM case
                    re_pkg_info = re_sw_info.findtext(
                        './version-information[component="MGD"]/release'
                    )
                    re_version = re.findall(r'(.*\d+)', re_pkg_info)[0]
            except Exception:
                re_version = None
        if model_info is None and re_model is not None:
            model_info = {}
        if re_model is not None:
            model_info[re_name] = re_model.upper()
        if hostname_info is None and re_hostname is not None:
            hostname_info = {}
        if re_hostname is not None:
            hostname_info[re_name] = re_hostname
        if junos_info is None and re_version is not None:
            junos_info = {}
        if re_version is not None:
            junos_info[re_name] = {'text': re_version,
                                   'object': version_info(re_version), }

        # Check to see if re_name is the RE we are currently connected to.
        # There are at least four cases to handle.
        this_re = False
        # 1) this device doesn't support the current_re fact and there's only
        #    one RE.
        if device.facts['current_re'] is None and len(si_rsp) == 1:
            this_re = True
        # 2) re_name is in the current_re fact. The easy case.
        elif re_name in device.facts['current_re']:
            this_re = True
        # 3) Some single-RE devices (discovered on EX2200 running 11.4R1)
        # don't include 'reX' in the current_re list. Check for this
        # condition and still set default hostname, model, and version
        elif (re_name == 're0' and 're1' not in device.facts['current_re'] and
              'master' in device.facts['current_re']):
            this_re = True
        # 4) For an lcc in a TX(P) re_name is 're0' or 're1', but the
        # current_re fact is ['lcc1-re0', 'member1-re0', ...]. Check to see
        # if any iri_name endswith the name of the
        elif this_re is False:
            for iri_name in device.facts['current_re']:
                if iri_name.endswith('-' + re_name):
                    this_re = True
                    break
        # Set hostname, model, and version facts if the RE we are currently
        # connected to.
        if this_re is True:
            if hostname is None:
                hostname = re_hostname
            if model is None:
                model = re_model.upper()
            if version is None:
                version = re_version

    if version is None:
        version = '0.0I0.0'
    ver_info = version_info(version)
    if junos_info is not None:
        if 're0' in junos_info:
            version_RE0 = junos_info['re0']['text']
        elif 'node0' in junos_info:
            version_RE0 = junos_info['node0']['text']
        if 're1' in junos_info:
            version_RE1 = junos_info['re1']['text']
        elif 'node1' in junos_info:
            version_RE1 = junos_info['node1']['text']

    return {'junos_info': junos_info,
            'hostname': hostname,
            'hostname_info': hostname_info,
            'model': model,
            'model_info': model_info,
            'version': version,
            'version_info': ver_info,
            'version_RE0': version_RE0,
            'version_RE1': version_RE1, }
