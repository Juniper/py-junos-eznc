## Release 2.1.5 - 31 July 2017
### Features Added:
- Single-RE sw install on multi-RE device using all_re argument to SW.install() #746
- Support platforms which have single-RE ISSU. #740
- Support Config.load() loading a configuration from a URL. #749
- SW.install() enhanced to install from a URL. #751
- Implement uptime property for Device instances. #752/#750
- Facts gathering support for Junos Node Slicing. #760

### Bugs Fixed:
- Refactor _exec_rpc() and handle boolean RPC arguments with a value of False. #739
- Add the _j2ldr instance variable to the Console class. #753
- Properly handle normalize argument to the open() Device method. #758/#757
- Setting no-resolve to true for faster ARP Table lookups. #762


## Release 2.1.4 - 23 June 2017
### Features Added:
- Optimize image copying in SW.safe_copy() #728 

### Bugs Fixed:
- unnecessary import cleanup #730
- Explicitly initialize jnpr.junos.facts sub-modules. #723/#731 
- socket.error handling for console->close() #734
- Ensure dev.timeout is an integer value. Addresses #735/#736
- Socket error fix #737


## Release 2.1.3 - 30 May 2017
### Features Added:
- Ephemeral config support #707
- Add a srx_cluster_redundancy_group fact. #711

### Bugs Fixed:
- ignore_warning fails when single <rpc-error> that is first child of <rpc-reply>. #712
- mode='telnet' did not logout non-cli user #713
- JSONLoadError was thrown when load valid JSON config #717/#718
- Fix XML normalization feature when using NETCONF over console. #719/#720
- Handle differences in |display xml rpc #722


## Release 2.1.2 - 2 May 2017
### Bugs Fixed:
- Doc badge was pointing to older version #694 
- Fix new-style fact gathering for SRX clusters. #697/#698
- Properly handle SW upgrades on multi-RE and/or multi-chassis systems when using new-style fact gathering. #700 
- Raise JSONLoadError if json config is malformed #706 
- Handle ConnectClosedError exception for lock() and unlock() #708 
- Return None when the RPC equiv is either str or unicode #721


## Release 2.1.1 - 28 Mar 2017
### Bugs Fixed:
- Fix regressions caused by `ignore_warning`. #691


## Release 2.1.0 - 22 Mar 2017
### Features Added:
- Enhanced fact gathering. Facts are now gathered "on demand." Additional facts are added. 
   The definition of facts and return values are properly documented. #638
- Support for YANG get RPCs. #672 
- Add an `ignore_warning` argument to suppress `RpcError` exceptions for warnings. #672/#685
- Enhanced the `sw.install()` method with basic ISSU and NSSU support using the issu and nssu
   boolean arguments. #606/#630/#632
   ** NSSU support has not yet been tested and should currently be considered experimental.
- Provide a master property and a re_name property for Device. #682
- Enhanced `reboot()` method to take an `all_re` boolean parameter which controls if only the connected
   Routing Engine, or all Routing Engines, are rebooted. #613
- Enhanced the warning message produced by the `cli()` method to recommend the corresponding
   `dev.rpc.<method>()` call. #603
- Add support for `update` parameter to configuration `load()` method. #681
- Added `directory_usage` to utils #629/#631/#636
- Adding support for NFX/JDM fact gathering. #652/#659
- Connected property. #664 

### Bugs Fixed:
- Updated the interface-name glob pattern to correctly match `et-<x>/<y>/<z>` interfaces
   in several tables and views. #609 
- Take care of special chars on screen during console connection. #610
- Address issue with fact gathering stopping when it encounters a problem. #615
- Minor typos fixed in `RuntimeError` exception message and in comments. #621
- Added `console_has_banner` parameter. #622
- Add CentOS Support to install instructions #623 
- Key value is needed in `_IsisAdjacencyLogTable` #627 
- Improved functionality and documentation of Docker build. #637/#673/#674/#677
- added remote port ID to lldp.yml (OP) #645
- Fix documentation for `rollback()` #647
- Fix for fact gathering pprint. #660/#661
- update ospf view, add bgp/inventory #665 
- Updated doc string for close function #686 
- Add Travis builds for Python 3.5 and 3.6 #687 
- StartShell.run to take this as None for non returning commands #680
- Modify ignore_warning return value to mimic normal RPC return value. #688


## Release 2.0.1
### Bugs Fixed:
- StartShell to take timeout (30 second by default) as paramter
- Proper exception handling in case of Console connection #595
- Fix: Config.lock() return exception when normalize is on
- Added microbadge badge for the Docker image #593
- Fix: print dev for Console conn was printing object not Device(....) #591
- Fix: To take care of special chars with StartShell->run function call #589
- Fix: ssh private key file to be considered for scp util #586
- Added Dockerfile to enable automated image builds on project commits #585


## Release 2.0.0
### Features Added:
- Console connection using PyEZ
- Python >=3.4 support
- Configuration Tables to Define and Configure Structured Resources
- JSON Config load
- FTP Utility

### Bugs Fixed:
- Multi RPC error
- various bug fixes

Refer below link for more details:
https://github.com/Juniper/py-junos-eznc/releases/tag/2.0.0


## Release 1.0

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

