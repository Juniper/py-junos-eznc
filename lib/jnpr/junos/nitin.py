
from jnpr.junos.factory.factory_loader import FactoryLoader
import yaml
from lxml import etree
from jnpr.junos.resources.syslog import SyslogTable

# Connect to device.

from jnpr.junos import Device
import logging
logging.basicConfig(level=logging.DEBUG)

from jnpr.junos.utils.sw import SW

# with Device(host='hmlcs27-7011.englab.juniper.net', user='root', password='MaRtInI', mode='telnet', port=7011,
with Device(host='10.221.149.77', user='regress', password='MaRtInI', mode='telnet', port=23,
            gather_facts=False) as dev:
    print dev.facts
    sw =SW(dev)
    sw.install(package='/var/tmp/nitin.sh', cleanfs=False)

# # from jnpr.junos.utils.start_shell import StartShell
#
# import logging
# logging.basicConfig(level=logging.DEBUG)
# with Device(hmode='serial', port=7011, gather_facts=False) as dev:
#     print dev.facts
#     print dev.cli("show version", warning=False)



# from jnpr.junos import Console
# from jnpr.junos.utils.config import Config
#
# with Console(mode='serial', port='7016') as dev:
#     print dev.cli("show version", warning=False)
#     cu = Config(dev)
#     cu.load(path='/var/tmp/mx.conf', format='text')
#     cu.pdiff()
#     cu.commit()

#     print dev.cli("show version", warning=False)
    # op = dev.rpc.get_interface_information()
    # print etree.tostring(op)

# print dev.facts
# import logging
# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger()

from jnpr.junos.console import Console
from jnpr.junos.utils.config import Config
from jnpr.junos.utils.fs import FS

# with Console(host='hmlcs27-7011.englab.juniper.net', user='root', password='Embe1mpls', mode='telnet', port='7011', gather_facts=True) as dev:
# # with Console(host='hmlcs27-7011.englab.juniper.net', user='root', mode='telnet', port='7011', gather_facts=True) as dev:
#     print dev.facts
    # print dev.cli("show version", warning=False)
    # cu = Config(dev)
    # cu.load(path='/Users/nitinkr/Documents/coffebite.conf')
    # cu.pdiff()
    # cu.commit()


import logging
# logging.basicConfig(level=logging.DEBUG)
# with Device(host='10.221.149.77', user='regress', password='MaRtInI', port='22', gather_facts=False) as dev:
# with Device(host='10.213.5.206', user='root', password='Embe1mpls', port='22', gather_facts=False) as dev:
#     print dev.facts
#     # print dev.cli("show route", warning=False)
#     op = dev.rpc.get_config()
#     print etree.tostring(op)

# cmd = ['show version', 'show interface terse']
#
# for i in cmd:
#     rootLogger.info(dev.cli(i, warning=False))


# print dev.facts
#
# # Create object of UserTable
# sl = SyslogTable(dev)
#
# sl.name = 'nitin'
# sl.contents_name = "any"
# sl.any = True
#
# sl.append()
# print etree.tostring(sl.get_table_xml())

#
# # Set field values
# gt.user = 'TestUser1'
# gt.uid = 1346
# gt.class_name = 'superuser'
# gt.password = 'MaRtInI'
#
# gt.append()
# # load configuration to running db
# gt.set()
#
# # Read data from device (using existing get() method)
# gt.get()
#
# print (gt)
#
# for item in gt:
#     print 'name:', item.user
#     print 'uid:', item.uid

# from jnpr.junos import Device
# from jnpr.junos.utils.sw import SW
# from pprint import pprint
# from jnpr.junos.utils.config import Config
# from lxml import etree
# from jnpr.junos.console import Console


# with Device(host='adora', user='root', password='Embe1mpls', port='22',
#              gather_facts=False) as dev:
#     op = dev.rpc.get_configuration()
#     print etree.tostring(op)
#
# dev = Device(host='10.221.149.77', user='regress', password='MaRtInI', port=22, gather_facts=False)
#
# cnf = """{
#     "configuration" : {
#         "system" : {
#             "services" : {
#                 "telnet" : [null]
#             }
#         }
#     }
# }"""
# dev.open()
# # pprint(dev.facts)
#
# cu = Config(dev)
# op = cu.load(cnf, format='json')
# print etree.tostring(op)
# dev.close()

#
# from jnpr.junos import Device
# from jnpr.junos.utils.config import Config
# from jnpr.junos.utils.fs import FS
# from getpass import getpass
#
# passwd = getpass('Enter password: ')
# with Device(host='hmlcs27-7016', user='regress', password=passwd, mode='telnet', port='7016') as dev:
#     print dev.cli("show version", warning=False)

    # op = dev.rpc.get_config(filter_xml=etree.XML('<configuration><system><services/></system></configuration>'), options={'format': 'json'})
    # print op
    # with SCP(dev, progress=True) as scp:
    #     scp.put('/var/tmp/test.txt', '/var/tmp/test.txt')

# from pprint import pprint
# from jnpr.junos import Device
# from lxml import etree
# import time
#
# dev = Device(host='10.221.149.77', user='root', password='Embe1mpls', gather_facts=False, port=22)
# dev.open()
# rsp = dev.rpc.request_idp_security_package_download()
# print etree.tostring(rsp)
#
# time.sleep(5)
# rsp = dev.rpc.request_idp_security_package_download(status=True)
# print etree.tostring(rsp)
# print rsp.findtext('.//secpack-download-status-detail')

# pprint(dev1.facts)
# dev1.timeout=300
# op = dev1.rpc.get_software_information()
# from lxml import etree
# print etree.tostring(op)
# dev1.close()




# from jnpr.junos.utils.config import Config
# from jnpr.junos.utils.fs import FS
# from jnpr.junos.console import Device
# from jnpr.junos.utils.sw import SW
# from jnpr.junos.op.routes import RouteTable
# from lxml import etree
#
# with Device(host='nms5-mx240-a', user='regress', password='MaRtInI', gather_facts=False) as dev:

# from jnpr.junos import Console
#
# with Console(host='10.221.149.77', user='regress', password='MaRtInI', mode='telnet', port='23', gather_facts=True) as dev:
#     print dev.facts
#     print dev.cli("show version", warning=False)
#     op = dev.rpc.get_interface_information()
#     print etree.tostring(op)



# from jnpr.junos import Device
# from jnpr.junos.utils.sw import SW
# from jnpr.junos.exception import ConnectError
#
# dev = Device('bng-ui-vm-87', user='regress', password='MaRtInI', gather_facts=False)
#
# dev.open()
#
# pkg = "/root/jpuppet-3.6.1_3.0_x86-32.tgz"
#
# sft= SW(dev)
#
# print (sft.validate(pkg))

from lxml import etree
from pprint import pprint
# from jnpr.junos.console import Device
#
# dev = Device('bng-ui-vm-94', user='regress', password='MaRtInI', gather_facts=False)
#
# dev.open()
# op = dev.cli("show interfaces em0 terse", warning=False)
# print op
# op = dev.cli("show interfaces em0 terse", warning=False, format='xml')
# print etree.tostring(op)
# op = dev.rpc.get_interface_information(interface_name='em0', terse=True)
# print etree.tostring(op)
# dev.close()