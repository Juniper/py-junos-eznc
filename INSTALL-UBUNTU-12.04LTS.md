### Installation on stock Ubuntu 12.04 LTS

The following are instructions for setting up a system starting from a stock Ubuntu 12.04 LTS system ISO image, downloaded from [here](http://www.ubuntu.com/download/desktop).  These instructions were tested on a 32-bit system, and using the _Junos PyEZ_ library version 0.0.5.

#### Step 1: Update system packages

Once you've installed the base OS, you should then perform the package update process.  This will update the existing packages on the system.  This will ensure that you have at least Python 2.7.3, as it is of the time of this writing.  You will then need to reboot your system to take effect.

#### Step 2: Install packages for Junos PyEZ

    sudo apt-get install -y curl git
    sudo apt-get install -y libxml2-dev libxslt-dev libyaml-dev python-dev
    sudo apt-get install -y python-setuptools
    curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | sudo python
    sudo pip install junos-eznc
    
#### Step 3: Verify 

Once you've completed the above step, you should be able to create a `Device` instance, connect to a Junos system, and display the "facts", as illustrated in the README.md file.

Enjoy!


