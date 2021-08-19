from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
import getpass
from lxml import etree
from pprint import pprint
from subprocess import PIPE
from subprocess import Popen
import cmd, sys
import os
import yaml

input_file = 'device_list-ALL.yml' #Yaml file containing all devices

#user = input("Junos OS username: ")
#passwd = getpass.getpass("Junos OS password: ")

for key, value in yaml.safe_load(open(input_file)).items():

#	with Device(host=value, user='<username>', passwd='<password>', port='22') as dev: 	# Option 1::Creds in clear text

#	with Device(host=value, user=user, passwd=passwd, port='22') as dev: 			# Option 2::Prompts for User/Passwd
	
	with Device(host=value, ssh_priv_key_file='~/.ssh/gitlab_ed25519') as dev: 		# Option 3::Using SSH Keys | Preferred

		try:
			dev.open()
		except ConnectError as err:
			print ('Cannot connect to device: {0}'.format(err))
			sys.exit(1)
		except Exception as err:
			print (err)
			sys.exit(1)
		data = dev.rpc.get_config(options={'database' : 'committed', 'format':'text'})
		
		config_file = open(key + '.txt', 'w')
		config_file.write(etree.tostring(data, encoding='unicode', method='xml'))
		print ('Successfully Collected Configuration from {}' .format(key))
		config_file.close()

dev.close()

cmds = ['mv *.txt /Users/me/git/network-configs/','cd /Users/me/git/network-configs/', 'git add --all','git commit -m "updating config files"', 'git push']
encoding = 'unicode'
p = Popen('/bin/bash', stdin=PIPE, stdout=PIPE, stderr=PIPE)

for cmd in cmds:
#In python 3+, str is a default for subprocess, therefore, we need to convert our command to bytes.
	p.stdin.write(bytes(cmd + "\n", 'utf-8'))
p.stdin.close()
print ('Pushing uncommitted config files to GitLab Completed')
