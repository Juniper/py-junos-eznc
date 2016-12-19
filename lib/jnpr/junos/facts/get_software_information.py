import re


class version_info(object):

    def __init__(self, verstr):
        """verstr - version string"""
        m1 = re.match('(.*?)([RBIXSF-])(.*)', verstr)
        self.type = m1.group(2)

        self.major = tuple(map(int, m1.group(1).split('.')))  # creates tuyple
        after_type = m1.group(3).split('.')
        self.minor = after_type[0]

        if 'X' == self.type:
            # assumes form similar to "45-D10", so extract the bits from this
            xm = re.match("(\d+)-(\w)(\d+)", self.minor)
            if xm is not None:
                self.minor = tuple(
                    [int(xm.group(1)), xm.group(2), int(xm.group(3))])
                if len(after_type) < 2:
                    self.build = None
                else:
                    self.build = int(after_type[1])
            # X type not hyphen format, perhaps "11.4X12.1", just extract build rev or set None
            else:
                if len(after_type) < 2:
                    self.build = None
                else:
                    self.build = int(after_type[1])

        elif ('I' == self.type) or ('-' == self.type):
            self.type = 'I'
            try:
                # assumes that we have a build/spin, but not numeric
                self.build = after_type[1]
            except:
                self.build = None
        else:
            try:
                self.build = int(after_type[1])   # assumes numeric build/spin
            except:
                self.build = after_type[0]  # non-numeric

        self.as_tuple = self.major + tuple([self.type, self.minor, self.build])
        self.v_dict = {'major': self.major, 'type': self.type,
                       'minor': self.minor, 'build': self.build}

    def __iter__(self):
        for key in self.v_dict:
            yield key, self.v_dict[key]

    def __repr__(self):
        retstr = "junos.version_info(major={major}, type={type}," \
                 " minor={minor}, build={build})".format(
                     major=self.major,
                     type=self.type,
                     minor=self.minor,
                     build=self.build
                 )
        return retstr


    def _cmp_tuple(self, other):
        length = len(self) if len(self) < len(other) else len(other)
        return self.as_tuple[0:length]


    def __len__(self):
        length = 0
        for component in self.as_tuple:
            if component is None:
                return length
            else:
                length += 1
        return length


    def __lt__(self, other):
        return self._cmp_tuple(other) < other


    def __le__(self, other):
        return self._cmp_tuple(other) <= other


    def __gt__(self, other):
        return self._cmp_tuple(other) > other


    def __ge__(self, other):
        return self._cmp_tuple(other) >= other


    def __eq__(self, other):
        return self._cmp_tuple(other) == other


    def __ne__(self, other):
        return self._cmp_tuple(other) != other


def version_yaml_representer(dumper, version):
    return dumper.represent_mapping(u'tag:yaml.org,2002:map', version.v_dict)


def _get_software_information(device):
    # See if device is VC Capable
    if device.facts['vc_capable'] is True:
        try:
            return device.rpc.cli("show version all-members", format='xml',
                                  normalize=True)
        except:
            pass
    # See if device understands "invoke-on all-routing-engines"
    try:
        return device.rpc.cli("show version invoke-on all-routing-engines",
                              format='xml', normalize=True)
    except:
        return device.rpc.get_software_information(normalize=True)


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'junos_info': 'A two-level dictionary where FILL IN',
            'hostname': 'A string containing the hostname of the current '
                        'Routing Engine.',
            'hostname_info': 'A dictionary keyed on Routing Engine name. The '
                             'value of each key is the hostname of the '
                             'Routing Engine.',
            'model': 'An uppercase string containing the chassis model of the '
                     'current Routing Engine.',
            'model_info': 'A dictionary keyed on Routing Engine name. The '
                          'value of each key is an uppercase string '
                          'containing the chassis model for the Routing '
                          'Engine.',
            'version': 'A string containing the Junos version of the current '
                       'Routing Engine.',
            'version_info': '',
            'version_RE0': '',
            'version_RE1': '', }


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
        re_name = re_sw_info.findtext('../re-name','re0')
        re_model = re_sw_info.findtext('./product-model')
        re_hostname = re_sw_info.findtext('./host-name')
        # First try the <junos-version> tag present in >= 15.1
        re_version = re_sw_info.findtext('./junos-version')
        if re_version is None:
            # For < 15.1, get version from the "junos" package.
            try:
                re_pkg_info = re_sw_info.xpath(
                    './package-information[name="junos"]/comment'
                )[0].text
                re_version = re.findall(r'\[(.*)\]', re_pkg_info)[0]
            except:
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
            junos_info[re_name] = { 'text': re_version,
                                    'object': version_info(re_version), }
        if re_name in device.facts['current_re']:
            if hostname is None:
                hostname = re_hostname
            if model is None:
                model = re_model.upper()
            if version is None:
                version = re_version

    if version is None:
        version = '0.0I0.0'
    ver_info = version_info(version)
    if 're0' in junos_info:
        version_RE0 = junos_info['re0']['text']
    if 're1' in junos_info:
        version_RE1 = junos_info['re1']['text']

    return {'junos_info': junos_info,
            'hostname': hostname,
            'hostname_info': hostname_info,
            'model': model,
            'model_info': model_info,
            'version': version,
            'version_info': ver_info,
            'version_RE0': version_RE0,
            'version_RE1': version_RE1, }
