
Vagrant
=======

[![Build Status](https://travis-ci.org/jeremyschulman/py-junos-eznc.png?branch=master)](https://travis-ci.org/jeremyschulman/py-junos-eznc)

Initially, the Vagrant environment supports Ansible as a provisioner, and only works with Linux and Mac OSX as the host OS.  It would be trivial to convert this to Chef or Puppet, but Ansible and Salt (the Python versions) either need a local client, or need a shell provisioner to bootstrap themselves (and then you lose out on Vagrant-aware provisioning).

----------


Prerequisites
---------


- **[vagrant](http://www.vagrantup.com) 1.2 or 1.3**
- **[virtualbox](http://www.virtualbox.org) 4.2 or 4.3**

> **NOTE:** Currently, only Ubuntu guests are supported for testing, as the packages and python/pip requirements need to be determined.**

#### <i class="icon-up"></i> `vagrant up precise` or `vagrant up raring`

This will bring up a new virtual machine, after downloading the image from [Opscode's Bento project](https://github.com/opscode/bento).

#### <i class="icon-refresh"></i> `vagrant provision precise` or `vagrant provision raring`

Provisions a VM, e.g. installs prerequisites and builds/installs py-junos-eznc.  *(Runs automatically after vagrant up.  Only needed when something fails.  Safe to run multiple times (idempotent))*

#### <i class="icon-terminal"></i> `vagrant ssh precise` or `vagrant ssh raring`

Creates an SSH session to the VM

#### <i class="icon-stop"></i> `vagrant halt` or `vagrant halt <boxname>`

Stop the VM(s).  Leaving the machine name out will perform the action on all created VMs.  This doesn't work with all commands.

#### <i class="icon-trash"></i> `vagrant destroy` or `vagrant destory <boxname>`

Delete the virtual machines from your system.  The actual base box files will remain in `.vagrant.d` in your home directory, and can be listed with `vagrant box list`, and removed with `vagrant box delete <boxname>`.


> **NOTE:** See [<i class="icon-share"></i> the official Vagrant documentation](http://docs.vagrantup.com/v2/) for a more detailed information


----------


Usage
---------------

 - Manually testing the build against different host platforms
 - Creating builders that can be called from [jenkins-ci](http://jenkins-ci.org/)
 - Determining the best practices for prerequisite and Python installs, e.g. CentOS 6 only supports Python up to 2.6 with [EPEL](http://fedoraproject.org/wiki/EPEL), so Python should be installed from source, with [pyenv](https://github.com/yyuu/pyenv) (as the local user, not system-wide), etc.
 - The Vagrantfile can be very easily modified to use cloud environments or VMware, as opposed to virtualbox