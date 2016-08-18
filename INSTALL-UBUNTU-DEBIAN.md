### Installation on stock Ubuntu and Debian

The following are instructions for setting up a system starting from stock system images.

These instructions were tested on a 64-bit systems from https://github.com/opscode/bento, and using the _Junos PyEZ_ library version 1.3.1.

Operating Systems
---------------
- Ubuntu 12.04
- Ubuntu 12.10
- Ubuntu 13.10
- Ubuntu 14.04
- Debian 7.4
- Debian 8.4


#### Step 1: Update package list

	sudo apt-get update

#### Step 2: Install OS packages required by Junos PyEZ and it's pre-requisite Python packages

    sudo apt-get install -y --force-yes python-dev libxslt1-dev libssl-dev libffi-dev

#### Step 3: Install the pip package manager from source

	wget https://bootstrap.pypa.io/get-pip.py -O - | sudo python
	
#### Step 4: Install Junos PyEZ

    sudo pip install junos-eznc
    
#### Step 5: Verify 

Once you've completed the above step, you should be able to create a `Device` instance, connect to a Junos system, and display the "facts", as illustrated in the README.md file.

Enjoy!


#### Installing from GitHub

Development code can be installed directly from GitHub based on any branch, commit, or tag.

***Steps 1 -3 are still required.***
#### Alternate Step 4: Install Junos PyEZ from GitHub

#### Step 4a: Install Git from OS packages 
    sudo apt-get install -y git

#### Step 4b: Install Junos PyEZ from GitHub
	sudo pip install git+https://github.com/Juniper/py-junos-eznc.git
	or
	sudo pip install git+https://github.com/Juniper/py-junos-eznc.git@<branch,tag,commit>
