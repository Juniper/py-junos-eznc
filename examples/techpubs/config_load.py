from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *

host = 'dc1a.example.com'
conf_file = 'configs/junos-config-add-op-script.conf'

def main():
    dev = Device(host=host)

    # open a connection with the device and start a NETCONF session
    try:
        dev.open()
    except Exception as err:
        print "Cannot connect to device:", err
        return

    dev.bind( cu=Config )

    # Lock the configuration, load configuration changes, and commit
    print "Locking the configuration"
    try:
        dev.cu.lock()
    except LockError:
        print "Error: Unable to lock configuration"
        dev.close()
        return

    print "Loading configuration changes"
    try:
        dev.cu.load(path=conf_file, merge=True)
    except ValueError as err:
        print err.message

    except Exception as err:
        if err.rsp.find('.//ok') is None:
            rpc_msg = err.rsp.findtext('.//error-message')
            print "Unable to load configuration changes: ", rpc_msg

        print "Unlocking the configuration"
        try:
                dev.cu.unlock()
        except UnlockError:
                print "Error: Unable to unlock configuration"
        dev.close()
        return

    print "Committing the configuration"
    try:
        dev.cu.commit()
    except CommitError:
        print "Error: Unable to commit configuration"
        print "Unlocking the configuration"
        try:
            dev.cu.unlock()
        except UnlockError:
            print "Error: Unable to unlock configuration"
        dev.close()
        return

    print "Unlocking the configuration"
    try:
         dev.cu.unlock()
    except UnlockError:
         print "Error: Unable to unlock configuration"


    # End the NETCONF session and close the connection
    dev.close()

if __name__ == "__main__":
        main()
