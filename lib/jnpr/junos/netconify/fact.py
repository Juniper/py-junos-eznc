import re
from lxml.builder import E
from lxml import etree


class Fact(object):

    def __init__(self, parent):
        self.rpc = parent.rpc
        self.facts = {}

    @property
    def items(self):
        return self.facts

    def version(self):
        rsp = self.rpc('get-software-information')
        self.swinfo = rsp  # keep this since we may want it later
        # extract the version
        # First try the <junos-version> tag present in >= 15.1

        swinfo= rsp.findtext('junos-version', default=None)
        if not swinfo:
            # For < 15.1, get version from the "junos" package.
            pkginfo = rsp.xpath(
                './/package-information[normalize-space(name)="junos"]/comment'
            )[0].text
            try:
                swinfo = re.findall(r'\[(.*)\]', pkginfo)[0]
            except:
                swinfo = "0.0I0.0"
        self.facts['version'] = swinfo

        # extract the host-name
        self.facts['hostname'] = rsp.xpath('.//host-name')[0].text

        # extract the product model/models
        product_model = rsp.xpath('//product-model')
        num_models = len(product_model)
        if num_models == 0:
            self.facts['model'] = None
        elif num_models == 1:
            self.facts['model'] = product_model[0].text.upper()
        else:
            fpc = lambda m: m.xpath('../../re-name')[0].text
            self.facts['models'] = dict((fpc(m), m.text.upper()) for m in product_model)

    def chassis(self):
        try:
            # try to get the chassis inventory. this will fail if the device
            # happens to be a QFX in 'node' mode, so use exception handling
            rsp = self.rpc('get-chassis-inventory')
            # keep this since we want to save the data to file
            self.inventory = rsp
            chas = rsp.find('chassis')
            sn = chas.findtext('serial-number')
            self.facts['model'] = chas.findtext('description').upper()

            # use the chassis level serial number, and if that doesn't exist
            # look for the 'Backplane' serial number
            self.facts['serialnumber'] = sn if sn is not None else \
                chas.xpath(
                    'chassis-module[name="Backplane"]/serial-number')[0].text
        except:
            # basically this catches the case if the device is a QFX in node mode;
            # the chassis-subsystem isn't running.  the hostname is the serial
            # nubmer
            self.facts['serialnumber'] = self.facts['hostname']
            pass

    def eth(self, ifname):
        cmd = E('get-interface-information',
                E.media(),
                E('interface-name', ifname))

        rsp = self.rpc(etree.tostring(cmd))[0]   # at physical-interface
        facts = self.facts

        facts[ifname] = {}
        facts[ifname]['macaddr'] = rsp.findtext('.//current-physical-address')
        facts[ifname]['ifindex'] = rsp.findtext('snmp-index')
        facts[ifname]['oper'] = rsp.findtext('oper-status')
        facts[ifname]['admin'] = rsp.findtext('admin-status')
        facts[ifname]['speed'] = rsp.findtext('speed')
        facts[ifname]['duplex'] = rsp.findtext('duplex')

        return facts[ifname]

    def gather(self):
        self.version()
        self.chassis()
