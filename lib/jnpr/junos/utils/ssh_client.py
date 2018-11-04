import paramiko


def open_ssh_client(junos):
    """
    This function is used to return a new paramiko SSH client that uses the same login method &
    credentials as the original Junos device instance.  The purpose of this function is to provide
    the caller with the complete paramiko library of functionality based on the returned SSH client.

    :param junos: jnpr.junos.Device instance
    :return: paramiko.SSHClient instance
    """

    # note, the following code was extracted from the scp module, and then the scp module
    # was refactored to use this function

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    config = {}
    kwargs = {}
    ssh_config = getattr(junos, '_sshconf_path')

    if ssh_config:
        config = paramiko.SSHConfig()
        config.parse(open(ssh_config))
        config = config.lookup(junos._hostname)

    sock = None

    if config.get("proxycommand"):
        sock = paramiko.proxy.ProxyCommand(config.get("proxycommand"))

    if junos._ssh_private_key_file is not None:
        kwargs['key_filename'] = junos._ssh_private_key_file

    use_port = int(junos._port) if junos._hostname == 'localhost' else 22

    client.connect(hostname=junos._hostname, port=use_port,
                   username=junos._auth_user,
                   password=junos._auth_password,
                   sock=sock, **kwargs)

    return client
