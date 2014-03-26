### Installation on stock FreeBSD

The following are instructions for setting up a system starting from a stock system images.

These instructions were tested on a 64-bit systems from https://github.com/opscode/bento, and using the _Junos PyEZ_ library version 0.0.5.

Operating Systems
---------------
- FreeBSD 9.2

#### Step 1: Install packages for Junos PyEZ

    sudo pkg_add -r py27-pip libxml2 libxslt
	
#### Step 2: Install Junos PyEZ

    sudo pip install junos-eznc
    
#### Step 3: Verify 

Once you've completed the above step, you should be able to create a `Device` instance, connect to a Junos system, and display the "facts", as illustrated in the README.md file.

Enjoy!


#### Installing from GitHub

Development code can be installed directly from GitHub based on any branch, commit, or tag.

***Packages from Step 1 are required.***

    sudo pkg_add -r git
	sudo pip install git+https://github.com/Juniper/py-junos-eznc.git
	
	or
	
	sudo pip install git+https://github.com/Juniper/py-junos-eznc.git@<branch,tag,commit>
