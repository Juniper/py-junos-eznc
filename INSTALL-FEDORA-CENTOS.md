### Installation on stock Fedora

The following are instructions for setting up a system starting from a stock system images.

These instructions were tested on a 64-bit systems from https://github.com/opscode/bento, and using the _Junos PyEZ_ library version 2.1.0.

Operating Systems
---------------
- Fedora 25
- Fedora 24
- CentOS 7.3
- CentOS 6.8

#### Step 1: Install Python and PIP

##### For Python 2.x:
###### For Fedora:
        sudo yum install python-pip python-devel
###### For CentOS:
        sudo yum install python-devel
        wget https://bootstrap.pypa.io/get-pip.py -O - | sudo python

##### For Python 3.x:
###### For Fedora:
        sudo yum install python3-devel
###### For CentOS:
        (Python 3 packages for CentOS are not provided.)

#### Step 1: Install packages for Junos PyEZ

    sudo yum install libxml2-devel libxslt-devel gcc openssl-devel libffi-devel redhat-rpm-config
	
#### Step 2: Install Junos PyEZ

##### For Python 2.x:
        sudo pip install junos-eznc

##### For Python 3.x:
        sudo pip3 install junos-eznc

#### Step 3: Verify 

Once you've completed the above step, you should be able to create a `Device` instance, connect to a Junos system, and display the "facts", as illustrated in the README.md file.

Enjoy!


#### Installing from GitHub

Development code can be installed directly from GitHub based on any branch, commit, or tag.

***Steps 1 -3 are still required.***
#### Alternate Step 4: Install Junos PyEZ from GitHub

#### Step 4a: Install Git from OS packages
    sudo yum install git

#### Step 4b: Install Junos PyEZ from GitHub

##### For Python 2.x:
	    sudo pip install git+https://github.com/Juniper/py-junos-eznc.git
	    or
	    sudo pip install git+https://github.com/Juniper/py-junos-eznc.git@<branch,tag,commit>

##### For Python 3.x:
	    sudo pip3 install git+https://github.com/Juniper/py-junos-eznc.git
	    or
	    sudo pip3 install git+https://github.com/Juniper/py-junos-eznc.git@<branch,tag,commit>
