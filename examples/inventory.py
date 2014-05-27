from jnpr.junos import Device

jdev = Device(user='jeremy', host='vsrx_cyan', password='jeremy1')
jdev.open()

inv = jdev.rpc.get_chassis_inventory()
print "model: %s" % inv.find('chassis/description').text
print "serial-number: %s" % inv.find('chassis/serial-number').text

# model: JUNOSV-FIREFLY
# serial-number: cf2eaceba2b7

jdev.close()
