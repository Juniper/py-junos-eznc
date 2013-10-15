___WORK IN PROGRESS - TINKER AT YOUR OWN PERIL___

___UNDER ACTIVE DEVELOPMENT, ITEMS WILL SHIFT AROUND WHILE COLLECTING FEEDBACK___


# ABOUT

A Python module that makes automating Junos devices over the NETCONF API "easy".  The goal of the microframework is to enable Netops/engineers the ability to create Python scripts without requiring "hardcore" programming knownledge or Junos XML.

# SUPPORTED PRODUCTS

This goal of this module is to provide a general purpose set of utilities and resources.  The module has been designed so that future contributors can easily "plug-in" thier extensions.  

The first pass of this module is targeting resource abstractions for the SRX firewall products.  These resource abstractions include:

 * Security zone interfaces
 * Security zone address-book items and sets
 * Security policy contexts and rule-sets
 * Security screens
 * Application items and sets
 * NAT simple source-NAT
 * NAT simple bi-directional static-NAT
 

# DEPENDENCIES

  * [Python 2.7](http://www.python.org/) - could work with others, but I haven't tested it
  * [ncclient](https://github.com/juniper/ncclient) (_Juniper edition_) - NETCONF base library
  * [lxml](http://lxml.de/index.html) - XML programming library
  * [jinja2](http://jinja.pocoo.org/docs) - templating library

# LICENSE

  BSD-2
  
# CONTRIBUTORS

  - Jeremy Schulman, @nwkautomaniac
