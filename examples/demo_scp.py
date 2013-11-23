import pdb
from pprint import pprint as pp
from lxml.builder import E
from lxml import etree

# junos "ez" module
from jnpr.junos import Device
from jnpr.junos.utils import SCP

dev = Device(user='jeremy', host='jnpr-dc-fw').open()

## now play around with dev object ...
## when done, you should issue dev.close()

##### -----------------------------------------------
##### approach #1 - using 'bind' and directly open,
##### use, close the scp object
##### -----------------------------------------------

def approach_1():
  dev.bind(scp=SCP)
  scp = dev.scp.open()

  # scp file from server to Junos device
  scp.put('jinstall.tgz','/var/tmp')
  scp.close()

##### -----------------------------------------------
##### approach #2 - using context manager
##### -----------------------------------------------

def approach_2():
  # copy a file from the Junos device onto the server
  with SCP(dev) as scp:
    scp.get('addrbook.conf')


### using a progress update function, pass the 
### :progress: keyword, per the SCP documentation.
### :approach_3: will copy a file to the Junos device
### and call the progress, every 10% of the copy, a
### print message will be displayed.  this also illustrates
### the use of 'static' variables in functions, yo!

def approach_3(src_path, dst_path='/var/tmp'):

  def scp_progress(_path, _total, _xfrd):
    # init static variable
    if not hasattr(scp_progress,'by10pct'): scp_progress.by10pct = 0

    # calculate current percentage xferd
    pct = int(float(_xfrd)/float(_total) * 100)

    # if 10% more has been copied, then print a message
    if 0 == (pct % 10) and pct != scp_progress.by10pct:
      scp_progress.by10pct = pct
      print "%s: %s / %s (%s%%)" % (_path,_xfrd,_total,str(pct))

  with SCP(dev, progress=scp_progress) as scp:
    scp.put(src_path, dst_path)

## example output:
# >>> approach_3('/usr/local/junos/packages/junos-vsrx-12.1X44-D20.3-domestic.tgz')
# junos-vsrx-12.1X44-D20.3-domestic.tgz: 22134784 / 221328723 (10%)
# junos-vsrx-12.1X44-D20.3-domestic.tgz: 44269568 / 221328723 (20%)
# junos-vsrx-12.1X44-D20.3-domestic.tgz: 66404352 / 221328723 (30%)
# junos-vsrx-12.1X44-D20.3-domestic.tgz: 88539136 / 221328723 (40%)
# junos-vsrx-12.1X44-D20.3-domestic.tgz: 110673920 / 221328723 (50%)
# junos-vsrx-12.1X44-D20.3-domestic.tgz: 132808704 / 221328723 (60%)
# junos-vsrx-12.1X44-D20.3-domestic.tgz: 154943488 / 221328723 (70%)
# junos-vsrx-12.1X44-D20.3-domestic.tgz: 177078272 / 221328723 (80%)
# junos-vsrx-12.1X44-D20.3-domestic.tgz: 199196672 / 221328723 (90%)
# junos-vsrx-12.1X44-D20.3-domestic.tgz: 221328723 / 221328723 (100%)
