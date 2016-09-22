[![PyPi Version](https://img.shields.io/pypi/v/junos-eznc.svg)](https://pypi.python.org/pypi/junos-eznc/) [![Documentation Status](https://readthedocs.org/projects/junos-pyez/badge/?version=2.0.1)](http://junos-pyez.readthedocs.io/en/2.0.1/?badge=2.0.1) [![Coverage Status](https://img.shields.io/coveralls/Juniper/py-junos-eznc.svg)](https://coveralls.io/r/Juniper/py-junos-eznc) [![Coverage Status](https://travis-ci.org/Juniper/py-junos-eznc.svg?branch=master)](https://travis-ci.org/Juniper/py-junos-eznc) [![](https://images.microbadger.com/badges/image/juniper/pyez.svg)](https://microbadger.com/images/juniper/pyez)

The repo is under active development.  If you take a clone, you are getting the latest, and perhaps not entirely stable code.  

# DOCUMENTATION

Official Documentation with examples, [here](http://www.juniper.net/techpubs/en_US/release-independent/junos-pyez/information-products/pathway-pages/index.html)

API Documentation hosted by [readthedocs](http://junos-pyez.readthedocs.org)

_Junos PyEZ_ wiki page, [here](https://techwiki.juniper.net/Projects/Junos_PyEZ).


# ABOUT

_Junos PyEZ_ is a Python library to remotely manage/automate Junos devices.  The user is ***NOT*** required: (a) to be a "Software Programmer™", (b) have sophisticated knowledge of Junos, or (b) have a complex understanding of the Junos XML API.  

This library was built for two types of users:

## For "Non-Programmers" - Python as a Power Shell

This means that "non-programmers", for example the _Network Engineer_, can use the native Python shell on their management server (laptop, tablet, phone, etc.) as their point-of-control for remotely managing Junos devices. The Python shell is an interactive environment that provides the necessary means to perform common automation tasks, such as conditional testing, for-loops, macros, and templates.  These building blocks are similar enough to other "shell" environments, like Bash, to enable the non-programmer to use the Python shell as a power-tool, rather than a programming language.  From the Python shell a user can manage Junos devices using native hash tables, arrays, etc. rather than device-specific Junos XML or resorting to 'screen scraping' the actual Junos CLI.

## For "Programmers" - Open and Extensible

There is a growing interest and need to automate the network infrastructure into larger IT systems.  To do so, traditional software programmers, DevOps, "hackers", etc. need an abstraction library of code to further those activities.  _Junos PyEZ_ is designed for extensibility so that the programmer can quickly and easily add new widgets to the library in support of their specific project requirements.  There is no need to "wait on the vendor" to provide new functionality.   _Junos PyEZ_ is not specifically tied to any version of Junos or any Junos product family.

# SUPPORT

For questions and general support, please visit our [Google Group](https://groups.google.com/forum/#!forum/junos-python-ez)

You can also post your query on stackoverflow with __pyez__ [tag](http://stackoverflow.com/questions/tagged/pyez)

For documentation and more usage examples, please visit the _Junos PyEZ_ project page, [here](http://forums.juniper.net/t5/Automation/Where-can-I-learn-more-about-Junos-PyEZ/ta-p/280496).

Issues and bugs can be opened in the repository.

# FEATURES

_Junos PyEZ_ is designed to provide the same capabilities as a user would have on the Junos CLI, but in an environment built for automation tasks.  These capabilities include, but are not limited to:

* Remote connectivity and management of Junos devices via NETCONF
* Provide "facts" about the device such as software-version, serial-number, etc.
* Retrieve "operational" or "run-state" information as Tables/Views
* Retrieve configuration information as Tables/Views
* Make configuration changes in unstructured and structured ways
* Provide common utilities for tasks such as secure copy of files and software updates

# NOTICE

As of release 2.0.0, _Junos PyEZ_ requires [ncclient](https://pypi.python.org/pypi/ncclient) version 0.5.2 or later.

# INSTALLATION

## PIP

Installation requires Python 2.6 or 2.7 or >=3.4 and associated `pip` tool

    pip install junos-eznc

Installing from Git is also supported (OS must have git installed).

	To install the latest MASTER code
	pip install git+https://github.com/Juniper/py-junos-eznc.git
	-or-
	To install a specific version, branch, tag, etc.
	pip install git+https://github.com/Juniper/py-junos-eznc.git@<branch,tag,commit>

## Docker

Move to the local directory which contains your script(s) and run the container

`docker run -it --rm --name pyez juniper/pyez sh`

Your local scripts will be mounted to /scripts in the container

`cd scripts`

## Upgrade

Upgrading has the same requirements as installation and has the same format with the addition of -UPGRADE

	pip install -U junos-eznc


## HELLO, WORLD

The following is a quick "hello, world" example to ensure that the software was installed correctly.  This code will simply connect to a device and display the known facts of the device, like serial-number, model, etc.

````python
from pprint import pprint
from jnpr.junos import Device

dev = Device(host='my_host_or_ipaddr', user='jeremy', password='jeremy123' )
dev.open()

pprint( dev.facts )

dev.close()
````
Example output for an SRX-210 device:
````python
>>> pprint(dev.facts)
{'2RE': False,
 'RE0': {'last_reboot_reason': '0x20:power-button soft power off',
         'model': 'RE-SRX210H',
         'status': 'OK',
         'up_time': '10 minutes, 3 seconds'},
 'domain': 'workflowsherpas.com'         
 'fqdn': 'srx210.workflowsherpas.com',
 'hostname': 'srx210',
 'ifd_style': 'CLASSIC',
 'model': 'SRX210H',
 'personality': 'SRX_BRANCH',
 'serialnumber': 'AD2909AA0096',
 'switch_style': 'VLAN',
 'version': '12.1X44-D10.4',
 'version_info': junos.versino_info(major=(12, 1), type=X, minor=(44, 'D', 10), build=4)}
````

# LICENSE

Apache 2.0

# CONTRIBUTORS

Juniper Networks is actively contributing to and maintaining this repo. Please contact jnpr-community-netdev@juniper.net for any queries.

*Contributors:*

[Nitin Kumar](https://github.com/vnitinv), [Edward Arcuri](https://github.com/sdndude), [Stacy Smith](https://github.com/stacywsmith)

* v2.0.0: [Ganesh Nalawade](https://github.com/ganeshnalawade), [Jainpriyal](https://github.com/Jainpriyal)

*Former Contributors:*

[Jeremy Schulman](https://github.com/jeremyschulman), [Rick Sherman](https://github.com/shermdog)
