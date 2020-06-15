import re
from jnpr.junos.facts.swver import version_info


def _get_swver(dev, facts):
    # See if we're VC Capable
    if facts["vc_capable"] is True:
        try:
            return dev.rpc.cli("show version all-members", format="xml")
        except:
            pass
    try:
        return dev.rpc.cli("show version invoke-on all-routing-engines", format="xml")
    except:
        return dev.rpc.get_software_information()


def facts_software_version(junos, facts):
    """
    The following facts are required:
        facts['master']

    The following facts are assigned:
        facts['hostname']
        facts['version']
        facts['version_<RE#>'] for each RE in dual-RE, cluster or VC system
        facts['version_info'] for master RE
    """

    x_swver = _get_swver(junos, facts)

    if not facts.get("model"):
        # try to extract the model from the version information
        facts["model"] = x_swver.findtext(".//product-model")

    # ------------------------------------------------------------------------
    # extract the version information out of the RPC response
    # ------------------------------------------------------------------------

    f_master = facts.get("master", "RE0")

    if x_swver.tag == "multi-routing-engine-results":
        # we need to find/identify each of the routing-engine (CPU) versions.
        if len(x_swver.xpath("./multi-routing-engine-item")) > 1:
            facts["2RE"] = True
        versions = []

        if isinstance(f_master, list):
            xpath = (
                './multi-routing-engine-item[re-name="{}"]/software-'
                "information/host-name".format(f_master[0].lower())
            )
        else:
            xpath = (
                './multi-routing-engine-item[re-name="{}"'
                "]/software-information/host-name".format(f_master.lower())
            )

        facts["hostname"] = x_swver.findtext(xpath)
        if facts["hostname"] is None:
            # then there the re-name is not what we are expecting; we should
            # handle this better, eh?  For now, just assume there is one
            # software-information element and take that host-name. @@@ hack.
            facts["hostname"] = x_swver.findtext(".//software-information/host-name")

        for re_sw in x_swver.xpath(".//software-information"):

            re_name = re_sw.xpath("preceding-sibling::re-name")[0].text

            # handle the cases where the "RE name" could be things like
            # "FPC<n>" or "ndoe<n>", and normalize to "RE<n>".
            re_name = re.sub(r"(\w+)(\d+)", "RE\\2", re_name)

            # First try the <junos-version> tag present in >= 15.1
            swinfo = re_sw.findtext("junos-version", default=None)
            if not swinfo:
                # For < 15.1, get version from the "junos" package.
                pkginfo = re_sw.xpath(
                    "package-information[normalize-space(name)=" '"junos"]/comment'
                )[0].text
                try:
                    swinfo = re.findall(r"\[(.*)\]", pkginfo)[0]
                except:
                    swinfo = "0.0I0.0"
            versions.append((re_name.upper(), swinfo))

        # now add the versions to the facts <dict>
        for re_ver in versions:
            facts["version_" + re_ver[0]] = re_ver[1]

        if f_master is not None:
            master = f_master[0] if isinstance(f_master, list) else f_master
            if "version_" + master in facts:
                facts["version"] = facts["version_" + master]
            else:
                facts["version"] = versions[0][1]
        else:
            facts["version"] = versions[0][1]

    else:
        # single-RE
        facts["hostname"] = x_swver.findtext("host-name")

        # First try the <junos-version> tag present in >= 15.1
        swinfo = x_swver.findtext(".//junos-version", default=None)
        if not swinfo:
            # For < 15.1, get version from the "junos" package.
            pkginfo = x_swver.xpath(
                './/package-information[normalize-space(name)="junos"]/comment'
            )[0].text
            try:
                swinfo = re.findall(r"\[(.*)\]", pkginfo)[0]
            except:
                swinfo = "0.0I0.0"
        facts["version"] = swinfo

    # ------------------------------------------------------------------------
    # create a 'version_info' object based on the master version
    # ------------------------------------------------------------------------

    facts["version_info"] = version_info(facts["version"])
