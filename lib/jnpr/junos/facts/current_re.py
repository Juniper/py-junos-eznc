from jnpr.junos.exception import RpcError
import re


def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {
        "current_re": "A list of internal routing instance hostnames "
        "for the current RE. These hostnames identify "
        "things like the RE's slot ('re0' or 're1'), the "
        "RE's mastership state ('master' or 'backup'), "
        "and node in a VC ('member0' or 'member1')",
    }


def get_facts(device):
    """
    The RPC-equivalent of show interfaces terse on private routing instance.
    """
    current_re = []

    try:
        if device.facts["_is_linux"]:
            rsp = device.rpc.get_system_nodes_information(normalize=True)

            # Get the RE (Active) list from the response
            res_list = rsp.xpath(
                "system-nodes-info-entry/system-node-info-node-attributes-list/"
                "system-node-info-node-attribute[text()='RE (Active)']/../.."
            )
            for re_ele in res_list:
                # Use the node-name element ot get RE name
                re_name = re_ele.xpath("system-node-info-node-name")
                current_re.append(re_name[0].text)
        else:
            rsp = device.rpc.get_interface_information(
                normalize=True,
                routing_instance="__juniper_private1__",
                terse=True,
            )

            # Get the local IPv4 addresses from the response.
            for ifa in rsp.iterfind(
                ".//address-family[address-family-name='inet']/"
                "interface-address/ifa-local"
            ):
                ifa_text = ifa.text
                if ifa_text is not None:
                    # Separate the IP from the mask
                    (ip, _, _) = ifa.text.partition("/")
                    if ip is not None:
                        # Use the _iri_hostname fact to map the IP address to
                        # an internal routing instance hostname.
                        if ip in device.facts["_iri_hostname"]:
                            for host in device.facts["_iri_hostname"][ip]:
                                if host not in current_re:
                                    current_re.append(host)
                        # An SRX platform in an HA cluster uses a different
                        # algorithm for assigning IRI IP addresses
                        elif device.facts["srx_cluster_id"] is not None:
                            try:
                                # Split the IRI IP into a list of 4 octets
                                octets = ip.split(".", 3)
                                # The 2nd octet will be cluster-id << 4
                                cluster_id_octet = str(
                                    (int(device.facts["srx_cluster_id"]) & 0x000F) << 4
                                )
                                # node0 will have an IP of
                                #     129.<cluster_id_octet>.0.1
                                # node1 will have an IP of
                                #     130.<cluster_id_octet>.0.1
                                # primary will have an IP of
                                #     143.<cluster_id_octet>.0.1
                                if (
                                    octets[1] == cluster_id_octet
                                    and octets[2] == "0"
                                    and octets[3] == "1"
                                ):
                                    host = None
                                    if octets[0] == "129":
                                        host = "node0"
                                    elif octets[0] == "130":
                                        host = "node1"
                                    elif octets[0] == "143":
                                        host = "primary"
                                    if host is not None and host not in current_re:
                                        current_re.append(host)
                            # Problem splitting IP into octets and indexing them.
                            # Keep looping to check the other IRI IPs.
                            except IndexError:
                                pass
    except RpcError:
        # Check to see if it's JDM of Junos Node slicing
        try:
            current_re_sw = device.rpc.get_software_information()
            if current_re_sw is not None:
                server_slot = current_re_sw.findtext(
                    './package-information[name="Server ' 'slot"]/comment'
                )
                slot_num = re.findall(r"Server slot : (\d+)", server_slot)[0]
                current_re = ["server" + slot_num]
        except Exception:
            pass

    # An empty list indicates a problem finding any current_re info.
    # Return None.
    if len(current_re) == 0:
        current_re = None

    return {
        "current_re": current_re,
    }
