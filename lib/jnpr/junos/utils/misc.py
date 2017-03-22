# utils/misc.py

import paramiko

def get_ssh_client(junos):
    """Get a Paramiko SSHClient using settings from the provided device."""
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # use junos._hostname since this will be correct if we are going
    # through a jumphost.

    # Retrieve ProxyCommand and IdentityFile
    sock = None
    key_file = junos._ssh_private_key_file
    ssh_config = junos._sshconf_path
    if ssh_config:
        config = paramiko.SSHConfig()
        config.parse(open(ssh_config))
        config = config.lookup(junos._hostname)
        if config.get("proxycommand"):
            sock = paramiko.proxy.ProxyCommand(config.get("proxycommand"))
        key_file = key_file or config.get("identityfile")

    ssh.connect(hostname=junos._hostname,
                port=(22, int(junos._port))[
                    junos._hostname == 'localhost'],
                username=junos._auth_user,
                password=junos._auth_password,
                key_filename=key_file,
                allow_agent=junos._allow_agent,
                sock=sock)
    return ssh
