from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import ConnectError, LockError, RpcError, CommitError, UnlockError

host = 'dc1a.example.com'


def main():
    dev = Device(host=host)
    # open a connection with the device and start a NETCONF session
    try:
        dev.open()
    except ConnectError as err:
        print "Cannot connect to device: {0}".format(err)
        return

    # Setup config object
    cu = Config(dev)

    # Lock the configuration
    print "Locking the configuration"
    try:
        cu.lock()
    except LockError as err:
        print "Unable to lock configuration: {0}".format(err)
        dev.close()
        return
    try:
        print "Rolling back the configuration"
        cu.rollback(rb_id=1)
        print "Committing the configuration"
        cu.commit()
    except CommitError as err:
        print "Error: Unable to commit configuration: {0}".format(err)
    except RpcError as err:
        print "Unable to rollback configuration changes: {0}".format(err)

    finally:
        print "Unlocking the configuration"
        try:
            cu.unlock()
        except UnlockError as err:
            print "Unable to unlock configuration: {0}".format(err)
        dev.close()
        return

if __name__ == "__main__":
    main()
