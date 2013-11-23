[![Build Status](https://travis-ci.org/jeremyschulman/py-junos-eznc.png?branch=master)](https://travis-ci.org/jeremyschulman/py-junos-eznc)

The repo is under active development on release 0.0.2.  If you take a clone, you are getting the latest, and perhaps not entirely stable code.  This code is not yet in PyPi.

## ABOUT

_Junos EZNC_ is a Python library that provides a collection of modules to further Junos automation without requiring: (a) the user to be a "Software Programmer™", (b) sophisticated knowledge of Junos, or (b) complex understanding of the Junos XML API.

The primary motivators for creating this framework:

### For "Non-Programmers", NoCLI

NoCLI = "Not Only CLI".  This means that "non-programmers", for example the _Network Engineer_, can use the native Python shell as their user-experience for managing Junos devices. The Python shell is an interactive environment that provides the necessary means to perform common automation tasks, such as conditional testing, for-loops, macros, and templates.  These building blocks are similar enough to other "shell" enviornments, like Bash, to enable the non-programmer to use the Python shell as a power-tool, rather than a programming language. 

### For "Programmers", an extensible microframework

There is a growing interest and need to automate the network infrastructure into larger IT systems.  To do so, traditional software programmers, DevOps, "hackers", etc. need an abstraction library of code to further those activities.  _Junos EZNC_ is designed for extensibility so that the programmer can quickly and easily add new widgets to the library in support of their specific project requirements.  There is no need to "wait on the vendor" to provide new functionality.   _Junos EZNC_ is not specifically tied to any version of Junos or any Junos product family. 

## INSTALLATION

This library is not yet in PyPi, so you will need to _git clone_ and run _python2.7 setup.py install_ or use _pip-2.7_ to install.  For complete instructions, see this [blog](http://forums.juniper.net/t5/Network-Automaniac/Python-for-Non-Programmers-Part-1/ba-p/216449). 

## HELLO, WORLD

The following is a quick "hello, world" example to ensure that the softare was installed correctly.  This code will simply connect to a device and display the known facts of the device, like serial-number, model, etc.

````python
from pprint import pprint
from jnpr.eznc import Netconf

dev = Netconf(host='my_host_or_ipaddr', user='jeremy', password='jeremy123' )
dev.open()

pprint( dev.facts )

dev.close()
````
## DOCUMENTATION

Please refer to the [_docs_](docs) directory.

## DEPENDENCIES

This module requires Python 2.7.  

  * [lxml](http://lxml.de/index.html) - XML programming library
  * [ncclient](https://github.com/juniper/ncclient) (_Juniper edition_) - NETCONF base library
  * [paramiko](https://github.com/paramiko/paramiko) - SSH library (also used by ncclient)
  * [scp](https://github.com/jbardin/scp.py) - SCP library
  * [jinja2](http://jinja.pocoo.org/docs) - templating library
  * [netaddr](https://pypi.python.org/pypi/netaddr/) - Network IPv4,IPv6 address library

## LICENSE

BSD-2
  
# CONTRIBUTORS

  - Jeremy Schulman (@nwkautomaniac), Core developer
