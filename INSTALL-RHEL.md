### Installation on RHEL

The following are instructions for setting up a system starting from a stock system images.

These instructions were tested on a 64-bit systems from https://github.com/opscode/bento, and using the _Junos PyEZ_ library version 2.6.4.

Operating Systems
---------------
- Red hat Enterprise Linux 8.1 (Ootpa)

#### Step 1: Install Python and PIP

##### For Python 3.x:
       dnf install python3-pip python3-wheel

#### Step 2: Install Junos PyEZ

##### For Python 3.x:
        sudo pip3 install junos-eznc

#### Step 3: Verify 

Once you've completed the above step, you should be able to create a `Device` instance, connect to a Junos system, and display the "facts", as illustrated in the README.md file.

Enjoy!

#### Installing from GitHub

Development code can be installed directly from GitHub based on any branch, commit, or tag.

***Step 1 and 3 still required.***
#### Alternate Step 4: Install Junos PyEZ from GitHub

#### Step 4a: Install Git from OS packages
        pip3 install git

#### Step 4b: Install Junos PyEZ from GitHub

##### For Python 3.x:
	    pip3 install git+https://github.com/Juniper/py-junos-eznc.git
