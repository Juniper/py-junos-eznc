import paramiko


def open_ssh_client(dev):
    """
    This function is used to return a new paramiko SSH client that uses the same login method &
    credentials as the original Junos device instance.  The purpose of this function is to provide
    the caller with the complete paramiko library of functionality based on the returned SSH client.
    :param dev: jnpr.junos.Device instance
    :return: paramiko.SSHClient instance
    """

    # note, the following code was extracted from the scp module, and then the scp module
    # was refactored to use this function
    ssh_client = paramiko.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # use junos._hostname since this will be correct if we are going
    # through a jumphost.

    config = {}
    kwargs = {}
    ssh_config = getattr(dev, "_sshconf_path")
    if ssh_config:
        config = paramiko.SSHConfig()
        with open(ssh_config) as open_ssh_config:
            config.parse(open_ssh_config)
        config = config.lookup(dev._hostname)

    sock = None
    if config.get("proxycommand"):
        sock = paramiko.proxy.ProxyCommand(config.get("proxycommand"))

    if dev._ssh_private_key_file is not None:
        kwargs["key_filename"] = dev._ssh_private_key_file

    # pick hostname from .ssh config if any
    hostname = config.get("hostname", dev._hostname)
    ssh_client.connect(
        hostname=hostname,
        port=(22, int(dev._port))[hostname == "localhost"],
        username=dev._auth_user,
        password=dev._auth_password,
        sock=sock,
        **kwargs
    )
    return ssh_client
