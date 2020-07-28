### Installation on stock FreeBSD

The following are instructions for setting up a system starting from a stock system image.

Operating Systems
---------------
- FreeBSD 10.4
- FreeBSD 11.1

FreeBSD contains py-junos-eznc in its official repositories. It could be installed from binary packages using pkg package manager or built from sources using ports collection.

## Installing from binary packages.

##### For Python 3.6
sudo pkg install py36-junos-eznc

## Installing from ports collection

#### For Python 3.6
sudo make -C /usr/ports/net-mgmt/py-junos-eznc install clean FLAVOR=py36

## Verify

Once you've completed the above step, you should be able to create a `Device` instance, connect to a Junos system, and display the "facts", as illustrated in the README.md file.

Enjoy!


## Installing from GitHub

Development code can be installed directly from GitHub based on any branch, commit, or tag.

***Packages from Steps 1 and 2 are required.***

    sudo pkg install git
	sudo pip install git+https://github.com/Juniper/py-junos-eznc.git
	
	or
	
	sudo pip install git+https://github.com/Juniper/py-junos-eznc.git@<branch,tag,commit>
