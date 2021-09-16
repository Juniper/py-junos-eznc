import re


class version_info(object):
    def __init__(self, verstr):
        """verstr - version string"""
        m1 = re.match("(.*?)([RBIXSF-])(.*)", verstr)
        self.type = m1.group(2)

        self.major = tuple(map(int, m1.group(1).split(".")))  # creates tuyple
        after_type = m1.group(3).split(".")
        self.minor = after_type[0]

        if "X" == self.type:
            # assumes form similar to "45-D10", so extract the bits from this
            xm = re.match("(\d+)-(\w)(\d+)", self.minor)
            if xm is not None:
                self.minor = tuple([int(xm.group(1)), xm.group(2), int(xm.group(3))])
                if len(after_type) < 2:
                    self.build = None
                else:
                    self.build = int(after_type[1])
            # X type not hyphen format, perhaps "11.4X12.1", just extract
            # build rev or set None
            else:
                if len(after_type) < 2:
                    self.build = None
                else:
                    self.build = int(after_type[1])

        elif ("I" == self.type) or ("-" == self.type):
            self.type = "I"
            try:
                # assumes that we have a build/spin, but not numeric
                self.build = after_type[1]
            except:
                self.build = None
        else:
            try:
                self.build = int(after_type[1])  # assumes numeric build/spin
            except:
                self.build = after_type[0]  # non-numeric

        self.as_tuple = self.major + tuple([self.type, self.minor, self.build])
        self.v_dict = {
            "major": self.major,
            "type": self.type,
            "minor": self.minor,
            "build": self.build,
        }

    def __iter__(self):
        for key in self.v_dict:
            yield key, self.v_dict[key]

    def __repr__(self):
        retstr = (
            "junos.version_info(major={major}, type={type},"
            " minor={minor}, build={build})".format(
                major=self.major, type=self.type, minor=self.minor, build=self.build
            )
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
    return dumper.represent_mapping(u"tag:yaml.org,2002:map", version.v_dict)


def provides_facts():
    """
    Doesn't really provide any facts.
    """
    return {}


def get_facts(device):
    """
    Doesn't get any facts.
    """
    return {}
