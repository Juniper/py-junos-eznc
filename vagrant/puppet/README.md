Vagrant/Puppet
=======

This example uses Puppet to install PyEz with PIP using either PiPy or Git.

----------


Prerequisites
---------


- **[vagrant](http://www.vagrantup.com) 1.5**
- **[virtualbox](http://www.virtualbox.org) 4.3**
- rsync on host

The first part of the provisioning process is a shell script to install Puppet.  These are provided at https://github.com/hashicorp/puppet-bootstrap/

Some editing of the files is necessary.  For example, centos_6_x.sh can be changed to fedora-20.sh with the following update:
```
REPO_URL="https://yum.puppetlabs.com/fedora/f20/products/x86_64/puppetlabs-release-20-10.noarch.rpm"
```


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
- Fedora 20
- Ubuntu 13.10
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
