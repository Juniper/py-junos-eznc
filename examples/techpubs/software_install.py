import os, sys, logging
from jnpr.junos import Device
from jnpr.junos.utils.sw import SW
from jnpr.junos.exception import *

host = 'dc1a.example.com'             
package = '/var/tmp/junos-install/jinstall-13.3R1.8-domestic-signed.tgz'
remote_path = '/var/tmp'
validate = True
logfile = '/var/log/junos-pyez/install.log'


def do_log(msg, level='info'):
    getattr(logging, level)(msg)

def update_progress(dev, report):
    # log the progress of the installing process
    do_log(report)


def main():

    # initialize logging
    logging.basicConfig(filename=logfile, level=logging.INFO,
                        format='%(asctime)s:%(name)s: %(message)s')
    logging.getLogger().name = host
    sys.stdout.write('Information logged in {0}\n'.format(logfile))

    # verify package exists
    if (os.path.isfile(package)):
        found = True
    else:
        msg = 'Software package does not exist: {0}. '.format(package)
        sys.exit(msg + '\nExiting program')


    dev = Device(host=host)
    try:
        dev.open()
    except Exception as err:
        sys.stderr.write('Cannot connect to device: {0}\n'.format(err))
        return
    
    # Increase the default RPC timeout to accommodate install operations
    dev.timeout = 300

    # Create an instance of SW
    sw = SW(dev)

    try:
        do_log('Starting the software upgrade process: {0}'.format(package))
        ok = sw.install(package=package, remote_path=remote_path, progress=update_progress, validate=validate)
    except Exception as err:
        msg = 'Unable to install software, {0}'.format(err) 
        do_log(msg, level='error')
    else:
        if ok is True:
            do_log('Software installation complete. Rebooting')
            rsp = sw.reboot() 
            do_log('Upgrade pending reboot cycle, please be patient.')
            do_log(rsp)   

    # End the NETCONF session and close the connection  
    dev.close()

if __name__ == "__main__":
    main()
