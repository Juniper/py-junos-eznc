Installation on OS X Mavericks
---------------
These instructions are community provided, tested with Python 2.7.5 and using the _Junos PyEZ_ library version 0.1.2.

### Operating Systems
- OS X Mavericks


When you upgrade your Mac to OS X Mavericks, Apple deletes your X11 and any addons under /Library/Python/2.7/site-packages.  There are plenty of posts on the Internet that describe how to restore your Python development environment, but this post will focus on the Juniper Junos PyEZ framework.
 
Github has Mac client available that includes command line tools and a native GUI app. - https://help.github.com/articles/set-up-git.

Install Homebrew - http://brew.sh.

#### Installation:
 
If you have never used Python on your Mac, you will want to install X11 & Xcode.  Some Python packages have dependencies that rely on these packages.
1. Install X11 – The latest image can be found here.
2. Install Xcode - https://developer.apple.com/xcode/ - you may have to register as a developer, but there is no charge to get access to Xcode.
3. After Xcode is installed, install the command line tools.
  1. Open a Terminal window.
  2. Type: ```xcode-select –install```
4. Install Git or the GitHub client.
5. Create a symbolic link so that the tools we are about to install will compile without issues.
  1. Open a Terminal Window.
  2. Type: ```sudo ln -s /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.9.sdk/usr/include/libxml2/libxml/ /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.9.sdk/usr/include/libxml```
  3. NOTE: this is a single, long string.
6. Install lxml with easy_install
  1. In a terminal window, type: ```sudo easy_install lxml```
  2. Easy_install works the best to install lxml
7. Download the ncclient repository from Github.
  1. From a terminal window, navigate to the ncclient download directory. I save to a GitHub directory under ~/Documents.
``` 
cd Documents/GitHub/ncclient
sudo python setup.py install
``` 
8.  Download the  py-junos-eznc repository from Github
  1. In the same terminal window, navigate to the py-junos-eznc directory
```
cd ../py-junos-eznc/
sudo python setup.py install
```
9.  Finally, I would install getpass, which is used in some scripts, using easy_install.
  1. sudo easy_install getpass