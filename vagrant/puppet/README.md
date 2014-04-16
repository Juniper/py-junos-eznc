Vagrant/Puppet
=======

This example uses Puppet to install PyEz with PIP using either PyPi or Git.

----------


Prerequisites
---------


- **[vagrant](http://www.vagrantup.com) 1.5**
- **[virtualbox](http://www.virtualbox.org) 4.3**
- rsync on host
 

Once Vagrant brings up the guest OS, two provisioners are executed in the following order:

1. Shell
  1. Install Puppet
2. Execute Puppet manifest
  1. Install dependencies with system package manager
  2. Install PyEZ with pip


For the script provisioner to install Puppet the required shell script must be present (as defined in the Vagrantfile). 

These are provided at https://github.com/hashicorp/puppet-bootstrap/

Some editing of the files is necessary.  

For example, centos_6_x.sh can be changed to fedora-20.sh with the following update:
```
REPO_URL="https://yum.puppetlabs.com/fedora/f20/products/x86_64/puppetlabs-release-20-10.noarch.rpm"
```


In testing the Debian script had to be modified.  A diff is provided below.

debian.sh
```
5a6,10
> if [ "$(id -u)" != "0" ]; then
>   echo "This script must be run as root." >&2
>   exit 1
> fi
> 
22,25d26
< if [ "$EUID" -ne "0" ]; then
<   echo "This script must be run as root." >&2
<   exit 1
< fi
```

Guest Operating Systems
---------------
- Ubuntu 12.04
- Ubuntu 12.10
- Ubuntu 13.10
- Fedora 19
- Fedora 20
- CentOS 6.5
- Debian 7.4
- FreeBSD 9.2


Usage
---------------
The Puppet module is initialized from manifests/default.pp.

PyEZ can be installed either via PyPi or Git.

PyPi
```
class{'pyez':
    mode => 'pypi',
	version => 'present', # Can be any version published to PyPi
  }
```

Git
```
class{'pyez':
    mode => 'git',
	version => 'present', # present for HEAD or any commit, tag, or branch.
  }
 ```
