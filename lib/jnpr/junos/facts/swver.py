import re


class version_info(object):

    def __init__(self, verstr):
        """verstr - version string"""
        m1 = re.match('(.*?)([RBIXS-])(.*)', verstr)
        self.type = m1.group(2)

        self.major = tuple(map(int, m1.group(1).split('.')))  # creates tuyple
        after_type = m1.group(3).split('.')
        self.minor = after_type[0]

        if 'X' == self.type:
            # assumes form similar to "45-D10", so extract the bits from this
            xm = re.match("(\d+)-(\w)(.*)", self.minor)
            self.minor = tuple(
                [int(xm.group(1)), xm.group(2), int(xm.group(3))])
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

        self.as_tuple = self.major + tuple([self.minor, self.build])
        self.v_dict = {
            'major': self.major,
            'type': self.type,
            'minor': self.minor,
            'build': self.build}

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
        bylen = {
            2: (self.as_tuple[0:2]),
            4: self.as_tuple
        }
        return bylen[len(other)]

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


def _get_swver(dev, facts):
    try:
        return dev.rpc.cli(
            "show version invoke-on all-routing-engines", format='xml')
    except:
        try:
            facts['vc_capable'] = True
            return dev.rpc.cli("show version all-members", format='xml')
        except:
            facts['vc_capable'] = False
            return dev.rpc.get_software_information()


def facts_software_version(junos, facts):
    """
    The following facts are required:
        facts['master']

    The following facts are assigned:
        facts['hostname']
        facts['version']
        facts['version_<RE#>'] for each RE in dual-RE, cluster or VC system
        facts['version_info'] for master RE
    """

    x_swver = _get_swver(junos, facts)

    if not facts.get('model'):
        # try to extract the model from the version information
        facts['model'] = x_swver.findtext('.//product-model')

    # ------------------------------------------------------------------------
    # extract the version information out of the RPC response
    # ------------------------------------------------------------------------

    f_master = facts.get('master', 'RE0')

    if x_swver.tag == 'multi-routing-engine-results':
        # we need to find/identify each of the routing-engine (CPU) versions.

        facts['2RE'] = True
        versions = []

        if isinstance(f_master, list):
            xpath = './multi-routing-engine-item[re-name="{0}"' \
                    ']/software-information/host-name'.format(
                        f_master[0].lower())
        else:
            xpath = './multi-routing-engine-item[re-name="{0}"' \
                    ']/software-information/host-name'.format(f_master.lower())

        facts['hostname'] = x_swver.findtext(xpath)
        if facts['hostname'] is None:
            # then there the re-name is not what we are expecting; we should
            # handle this better, eh?  For now, just assume there is one
            # software-information element and take that host-name. @@@ hack.
            facts['hostname'] = x_swver.findtext(
                './/software-information/host-name')

        for re_sw in x_swver.xpath('.//software-information'):

            re_name = re_sw.xpath('preceding-sibling::re-name')[0].text

            # handle the cases where the "RE name" could be things like
            # "FPC<n>" or "ndoe<n>", and normalize to "RE<n>".
            re_name = re.sub(r'(\w+)(\d+)', 'RE\\2', re_name)

            try:
                pkginfo = re_sw.xpath(
                    'package-information[normalize-space(name)="junos"]/comment'
                )[0].text
            except IndexError:
                # occam and some build is not having tag <name>junos</name>
                pkginfo = re_sw.findtext('junos-version')

            try:
                versions.append(
                    (re_name.upper(),
                     re.findall(
                         r'\[?(.*)\]?',
                         pkginfo)[0]))
            except:
                versions.append((re_name.upper(), "0.0I0.0"))

        # now add the versions to the facts <dict>
        for re_ver in versions:
            facts['version_' + re_ver[0]] = re_ver[1]

        if f_master is not None:
            master = f_master[0] if isinstance(f_master, list) else f_master
            facts['version'] = facts['version_' + master]
        else:
            facts['version'] = versions[0][1]

    else:
        # single-RE
        facts['hostname'] = x_swver.findtext('host-name')

        pkginfo = x_swver.xpath(
            './/package-information[normalize-space(name)="junos"]/comment'
        )[0].text
        facts['version'] = re.findall(r'\[(.*)\]', pkginfo)[0]

    # ------------------------------------------------------------------------
    # create a 'version_info' object based on the master version
    # ------------------------------------------------------------------------

    facts['version_info'] = version_info(facts['version'])


def version_yaml_representer(dumper, version):
    return dumper.represent_mapping(u'tag:yaml.org,2002:map', version.v_dict)
