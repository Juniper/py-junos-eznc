Vagrant
=======

The intent of the Vagrant directory is to provide multiple examples of installing PyEZ using tools such as Ansible, Puppet, and Chef.    The host and guest operating systems will vary based on capability of each provisioner, and updates are provided as best effort.

----------


Prerequisites
---------


- **[vagrant](http://www.vagrantup.com) 1.5**
- **[virtualbox](http://www.virtualbox.org) 4.3**

#### `vagrant status`

Display status of configured machines.

#### <i class="icon-up"></i> `vagrant up` or `vagrant up <boxname>`

This will bring up a new virtual machine, after downloading the image from [Opscode's Bento project](https://github.com/opscode/bento).

#### `vagrant ssh <boxname>`

Creates an SSH session to the VM

#### `vagrant halt` or `vagrant halt <boxname>`

Stop the VM(s).  Leaving the machine name out will perform the action on all created VMs.  This doesn't work with all commands.

#### `vagrant destroy` or `vagrant destory <boxname>`

Delete the virtual machines from your system.  The actual base box files will remain in `.vagrant.d` in your home directory, and can be listed with `vagrant box list`, and removed with `vagrant box delete <boxname>`.

#### `vagrant provision <boxname>`

Provisions a VM, e.g. installs prerequisites and builds/installs py-junos-eznc.  *(Runs automatically after vagrant up.  Only needed when something fails.  Safe to run multiple times (idempotent))*


> **NOTE:** See [<i class="icon-share"></i> the official Vagrant documentation](http://docs.vagrantup.com/v2/) for a more detailed information


----------


Usage
---------------

 - Manually testing the build against different host platforms
 - Creating builders that can be called from [jenkins-ci](http://jenkins-ci.org/)
 - Determining the best practices for prerequisite and Python installs, e.g. CentOS 6 only supports Python up to 2.6 with [EPEL](http://fedoraproject.org/wiki/EPEL), so Python should be installed from source, with [pyenv](https://github.com/yyuu/pyenv) (as the local user, not system-wide), etc.
 - The Vagrantfile can be very easily modified to use cloud environments or VMware, as opposed to virtualbox
