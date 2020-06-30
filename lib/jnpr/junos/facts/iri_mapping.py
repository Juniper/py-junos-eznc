def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {
        "_iri_hostname": "A dictionary keyed by internal routing instance "
        "ip addresses. The value of each key is the "
        "internal routing instance hostname for the ip",
        "_iri_ip": "A dictionary keyed by internal routing instance "
        "hostnames. The value of each key is the internal "
        "routing instance ip for the hostname",
    }


def get_facts(device):
    """
    Gathers facts from a <file-show/> RPC on the '/etc/hosts.junos' file.
    """
    iri_hostname = None
    iri_ip = None

    rsp = device.rpc.file_show(filename="/etc/hosts.junos", normalize=False)

    if rsp is not None:
        hosts_file_content = rsp.findtext(".", default="")
        if hosts_file_content is not None:
            for line in hosts_file_content.splitlines():
                (line, _, _) = line.partition("#")
                components = line.split(None)
                if len(components) > 1:
                    ip = components[0]
                    hosts = components[1:]
                    if iri_hostname is None:
                        iri_hostname = {}
                    if iri_ip is None:
                        iri_ip = {}
                    if ip in iri_hostname:
                        iri_hostname[ip] += hosts
                    else:
                        iri_hostname[ip] = hosts
                    for host in hosts:
                        if host in iri_ip:
                            iri_ip[host].append(ip)
                        else:
                            iri_ip[host] = [ip]
                    for host in hosts:
                        # Handle templates with %d
                        if "%d" in host:
                            octets = ip.split(".", 3)
                            for count in range(255):
                                t_ip = (
                                    octets[0]
                                    + "."
                                    + octets[1]
                                    + "."
                                    + str(count)
                                    + "."
                                    + octets[3]
                                )
                                t_host = host.replace("%d", str(count))
                                if t_ip in iri_hostname:
                                    iri_hostname[t_ip].append(t_host)
                                else:
                                    iri_hostname[t_ip] = [t_host]
                                if t_host in iri_ip:
                                    iri_ip[t_host].append(t_ip)
                                else:
                                    iri_ip[t_host] = [t_ip]

    return {
        "_iri_hostname": iri_hostname,
        "_iri_ip": iri_ip,
    }
