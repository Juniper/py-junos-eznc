### Installation on stock FreeBSD

The following are instructions for setting up a system starting from a stock system image.

These instructions were tested on a 64-bit systems from https://github.com/opscode/bento, and using the _Junos PyEZ_ library version 2.1.0.

Operating Systems
---------------
- FreeBSD 10.3
- FreeBSD 11.0

#### Step 1: Install Python and PIP

##### For Python 2.7:
        sudo pkg install py27-pip
##### For Python 3.5:
        sudo pkg install python35
        curl https://bootstrap.pypa.io/get-pip.py | sudo /usr/local/bin/python3.5

#### Step 2: Install packages for Junos PyEZ

    sudo pkg install libxml2 libxslt
	
#### Step 3: Install Junos PyEZ

    sudo pip install junos-eznc
    
#### Step 4: Verify

Once you've completed the above step, you should be able to create a `Device` instance, connect to a Junos system, and display the "facts", as illustrated in the README.md file.

Enjoy!


#### Installing from GitHub

Development code can be installed directly from GitHub based on any branch, commit, or tag.

***Packages from Steps 1 and 2 are required.***

    sudo pkg install git
	sudo pip install git+https://github.com/Juniper/py-junos-eznc.git
	
	or
	
	sudo pip install git+https://github.com/Juniper/py-junos-eznc.git@<branch,tag,commit>
