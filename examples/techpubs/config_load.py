from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import ConnectError, LockError, UnlockError, ConfigLoadError, CommitError

host = 'dc1a.example.com'
conf_file = 'configs/junos-config-add-op-script.conf'


def main():
    # open a connection with the device and start a NETCONF session
    try:
        dev = Device(host=host)
        dev.open()
    except ConnectError as err:
        print "Cannot connect to device: {0}".format(err)
        return

    dev.bind(cu=Config)

    # Lock the configuration, load configuration changes, and commit
    print "Locking the configuration"
    try:
        dev.cu.lock()
    except LockError as err:
        print "Unable to lock configuration: {0}".format(err)
        dev.close()
        return

    print "Loading configuration changes"
    try:
        dev.cu.load(path=conf_file, merge=True)
    except (ConfigLoadError, Exception) as err:
        print "Unable to load configuration changes: {0}".format(err)
        print "Unlocking the configuration"
        try:
                dev.cu.unlock()
        except UnlockError:
            print "Unable to unlock configuration: {0}".format(err)
        dev.close()
        return

    print "Committing the configuration"
    try:
        dev.cu.commit(comment='Loaded by example.')
    except CommitError as err:
        print "Unable to commit configuration: {0}".format(err)
        print "Unlocking the configuration"
        try:
            dev.cu.unlock()
        except UnlockError as err:
            print "Unable to unlock configuration: {0}".format(err)
        dev.close()
        return

    print "Unlocking the configuration"
    try:
        dev.cu.unlock()
    except UnlockError as err:
        print "Unable to unlock configuration: {0}".format(err)

    # End the NETCONF session and close the connection
    dev.close()

if __name__ == "__main__":
        main()
