### Installation on stock Ubuntu and Debian

The following are instructions for setting up a system starting from a stock system images.

These instructions were tested on a 64-bit systems from https://github.com/opscode/bento, and using the _Junos PyEZ_ library version 0.0.5.

Operating Systems
---------------
- Ubuntu 12.04
- Ubuntu 12.10
- Ubuntu 13.10
- Debian 7.4


#### Step 1: Update package list

	sudo apt-get update

#### Step 2: Install packages for Junos PyEZ

    sudo apt-get install -y python-pip python-dev libxml2-dev libxslt-dev
	
#### Step 3: Install Junos PyEZ

    sudo pip install junos-eznc
    
#### Step 4: Verify 

Once you've completed the above step, you should be able to create a `Device` instance, connect to a Junos system, and display the "facts", as illustrated in the README.md file.

Enjoy!


#### Installing from GitHub

Development code can be installed directly from GitHub based on any branch, commit, or tag.

***Packages from Step 2 are required.***

    sudo apt-get install -y git
	sudo pip install git+https://github.com/Juniper/py-junos-eznc.git
	
	or
	
	sudo pip install git+https://github.com/Juniper/py-junos-eznc.git@<branch,tag,commit>
