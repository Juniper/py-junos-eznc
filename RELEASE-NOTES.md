# Release 1.0

# Junos PyEZ Overview

The Junos PyEZ project is an open-source Apache 2.0 library for the Python programming language.  The purpose of this "micro-framework" library is to enable the networking professional community to effectively utilize the Junos OS NETCONF and XML APIs.    

The Junos PyEZ library can be used on any number of server environments supporting Python 2.6 and 2.7.  

At the time of this writing, Junos PyEZ is not distributed on devices running Junos OS.

For feature documentation and community support, refer to the following URLs:
  * Project Page hosted on the Juniper Networks TechWiki:
http://techwiki.juniper.net/Automation_Scripting/Junos_PyEZ
  * Source code hosted on Github:
https://github.com/Juniper/py-junos-eznc
  * Support forum hosted using Google Groups:
https://groups.google.com/forum/#!forum/junos-python-ez

# Installing Junos PyEZ
Junos PyEZ can be installed directly from the PyPi repository by typing `pip install junos-eznc` at the system command line.   

The "pip" installation process also installs any related dependent Python modules and libraries.  Depending on your specific system, you might need to have the prerequisite build tools installed as well.

For the complete set of installation instructions for various platforms, see the Junos PyEZ project documentation at https://techwiki.juniper.net/Automation_Scripting/Junos_PyEZ/Installation.

# Recommended Junos Release
Junos PyEZ can be used with any device running Junos OS, because they all support the NETCONF and Junos XML APIs.   To take full advantage of the Junos PyEZ features, we recommend using Junos OS Release 11.4 or later release - see "Known Limitations and Restrictions" section for details.  For more information about Junos OS releases, refer to the Juniper Networks technical documentation site at https://www.juniper.net/techpubs/en_US/release-independent/junos/information-products/pathway-pages/junos/product/index.html .

# Supported Python Releases
The Junos PyEZ library has been tested with Python versions 2.6 and 2.7.  
At the time of this writing PyEZ is not supported in Python 3.x environments.  This restriction is due to dependencies on other Python modules, such as ncclient, that do not support Python 3.x.    

# Known Limitations and Restrictions
## General
  * Junos PyEZ maintains a "timeout" mechanism for each executed command and response pair.  The default timeout is 30 seconds.  You can override the default by using the Device.timeout property.  If a timeout does occur, a timeout exception is raised.  
  * Some devices running Junos OS might disconnect the NETCONF session due to inactivity.  This behavior has been observed on SRX Series Services Gateways.  In such cases, an exception is raised upon execution of the next command.  The Junos PyEZ library does not reconnect to the device in these inactivity scenarios.  However, you can call Device.open() to reconnect.
  * Command execution is synchronous and blocking.  The underlying NETCONF transport library is the ncclient module.  If your application requires asynchronous or nonblocking execution logic, you should investigate other libraries to wrap around the PyEZ framework such as Twisted or Python Threads.
  * The `Device.cli()` method is intended to be used with interactive python, and as a means to facilitate the interactive experience as needed.  Please do not use this for "screen-scraping" the CLI output for automation purposes.

## Version-Specific Limitations
A couple software version-dependent limitations that must be noted:
* 11.4 - This is the first release where the Junos XML API supports the ability to retrieve the command output in text (CLI) format.  Prior to Junos OS Release 11.4, the response output was in XML.  If you use the Device.cli() feature, note that this only works with Junos OS Release 11.4 and later releases. 
* 11.4 - This is the first release where the Junos XML API supports the ability to load configuration changes using Junos OS set commands.  

## Restrictions
### Primary Routing Engine
For devices with multiple Routing Engines, you can only connect to the primary Routing Engine.  If you attempt to connect to the backup Routing Engine, the Device.open() method fails with an exception.

### Junos OS Software Upgrade
The primary restriction is on software-install functionality provided by the jnpr.junos.utils.sw module.  The software-install process is currently designed to support simple deployment scenarios.  The expected use case for this software is deploying new equipment.  The following scenarios are supported:
* Standalone devices with a single Routing Engine, for example EX4200 switches
* Standalone devices equipped with dual Routing Engines, for example MX960 routers
* EX Series Virtual Chassis in non-mixed-mode configurations (all devices use the same Junos OS software package)
* Deployment configurations that do not have any form of "in-service" features enabled, such as unified ISSU and NSSU.

The following scenarios are known not to be supported:
* SRX Series chassis clusters
* EX Series Virtual Chassis in mixed-mode configurations (devices use different Junos OS software packages)
* Virtual Chassis Fabric (VCF)
* MX Series Virtual Chassis 
* Any deployments with "in-service" configurations enabled (such as unified ISSU or NSSU)

