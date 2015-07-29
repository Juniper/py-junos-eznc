from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *

host = 'dc1a.example.com'

def main():
    dev = Device(host=host)
    # open a connection with the device and start a NETCONF session
    try:
        dev.open()
    except Exception as err:
        print "Cannot connect to device:", err
        return

    cu=Config(dev)

    # Lock the configuration
    print "Locking the configuration"
    try:
        cu.lock()
    except LockError:
        print "Error: Unable to lock configuration"
        dev.close()
        return


    try:
        print "Rolling back the configuration"
        cu.rollback(rb_id=1)
        print "Committing the configuration"
        cu.commit()
    except ValueError as err:
        print err.message
    except CommitError:
        print "Error: Unable to commit configuration"
    except Exception as err:
        if err.rsp.find('.//ok') is None:
            rpc_msg = err.rsp.findtext('.//error-message')
            print "Unable to rollback configuration changes: ", rpc_msg
    finally:
        print "Unlocking the configuration"
        try:
            cu.unlock()
        except UnlockError:
            print "Error: Unable to unlock configuration"
        dev.close()
        return

if __name__ == "__main__":
    main()

