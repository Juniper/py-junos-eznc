# ABOUT

A Python module that makes automating Junos devices over the NETCONF API "easy".  The goal of the microframework is to enable Netops/engineers the ability to create Python scripts without requiring "hardcore" programming knownledge or Junos XML.

# STATUS

___WORK IN PROGRESS - UNDER ACTIVE DEVELOPMENT___

# SUPPORTED PRODUCTS

This goal of this module is to provide a general purpose set of utilities and resources.  The module has been designed so that future contributors can easily "plug-in" thier extensions.  This module should work with __ALL__ Junos based products.  There are specific _Resources_ that are platform/function specific.

### SRX

The first pass of this module is targeting resource abstractions for the SRX firewall products.  These resource abstractions include:

 * Security zone interfaces
 * Security zone address-book items and sets
 * Security policy contexts and rule-sets
 * Security screens
 * Security application items and sets
 * Source NAT address pools, rule-sets, and rules
 * Static NAT rule-sets and rules
 
# HACKING

If you'd like to hack on this code or try it out, you will need to install the [ncclient](https://github.com/juniper/ncclient) module from the Juniper github repo directly.  You will then need to install this module and source the `env-setup.sh` file.  This will set your `PYTHONPATH` variable so it picks up the local module.


# DEPENDENCIES

  * [Python 2.7](http://www.python.org/) - could work with others, but I haven't tested it
  * [ncclient](https://github.com/juniper/ncclient) (_Juniper edition_) - NETCONF base library
  * [lxml](http://lxml.de/index.html) - XML programming library
  * [jinja2](http://jinja.pocoo.org/docs) - templating library

# LICENSE

  BSD-2
  
# CONTRIBUTORS

  - Jeremy Schulman, @nwkautomaniac
