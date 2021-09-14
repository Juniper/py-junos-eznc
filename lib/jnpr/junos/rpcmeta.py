import re
import sys
from lxml import etree
from lxml.builder import E
from jnpr.junos import jxml as JXML


class _RpcMetaExec(object):

    # -----------------------------------------------------------------------
    # CONSTRUCTOR
    # -----------------------------------------------------------------------

    def __init__(self, junos):
        """
        ~PRIVATE CLASS~
        creates an RPC meta-executor object bound to the provided
        ez-netconf :junos: object
        """
        self._junos = junos

    # -----------------------------------------------------------------------
    # get_config
    # -----------------------------------------------------------------------

    def get_config(
        self,
        filter_xml=None,
        options={},
        model=None,
        namespace=None,
        remove_ns=True,
        **kwargs
    ):
        """
        retrieve configuration from the Junos device

        .. code-block:: python

           dev.rpc.get_config()
           dev.rpc.get_config(filter_xml='<system><services/></system>')
           dev.rpc.get_config(filter_xml='system/services')
           dev.rpc.get_config(
               filter_xml=etree.XML('<system><services/></system>'),
               options={'format': 'json'})
           # to fetch junos as well as yang model configs
           dev.rpc.get_config(model=True)
           # openconfig yang example
           dev.rpc.get_config(filter_xml='bgp', model='openconfig')
           dev.rpc.get_config(filter_xml='<bgp><neighbors></neighbors></bgp>',
                            model='openconfig')
           # custom yang example
           dev.rpc.get_config(filter_xml='l2vpn', model='custom',
                        namespace="http://yang.juniper.net/customyang/l2vpn")
           # ietf yang example
           dev.rpc.get_config(filter_xml='interfaces', model='ietf')
           # ietf-softwire yang example
           dev.rpc.get_config(filter_xml='softwire-config', model='ietf',
                              namespace="urn:ietf:params:xml:ns:yang:ietf-softwire",
                              options={'format': 'json'})


        :filter_xml: fully XML formatted tag which defines what to retrieve,
                     when omitted the entire configuration is returned;
                     the following returns the device host-name configured
                     with "set system host-name"

        .. code-block:: python

           config = dev.rpc.get_config(filter_xml=etree.XML('''
               <configuration>
                   <system>
                       <host-name/>
                   </system>
               </configuration>'''))

        :options: is a dictionary of XML attributes to set within the
                  <get-configuration> RPC; the following returns the device
                  host-name either configured with "set system host-name"
                  and if unconfigured, the value inherited from
                  apply-group re0|re1, typical for multi-RE systems

        .. code-block:: python

           config = dev.rpc.get_config(filter_xml=etree.XML('''
                        <configuration>
                            <system>
                                <host-name/>
                            </system>
                        </configuration>'''),
                 options={'database':'committed','inherit':'inherit'})

        :param str model: Can provide yang model openconfig/custom/ietf. When
                model is True and filter_xml is None, xml is enclosed under
                <data> so that we get junos as well as other model
                configurations

        :param str namespace: User can have their own defined namespace in the
                custom yang models, In such cases they need to provide that
                namespace so that it can be used to fetch yang modeled configs

        :param bool remove_ns: remove namespaces, if value assigned is False,
                function will return xml with namespaces. The same xml
                returned can be loaded back to devices. This comes handy in
                case of yang based configs

        .. code-block:: python

           dev.rpc.get_config(filter_xml='bgp', model='openconfig',
                        remove_ns=False)
        """

        nmspaces = {
            "openconfig": "http://openconfig.net/yang/",
            "ietf": "urn:ietf:params:xml:ns:yang:ietf-",
        }

        rpc = E("get-configuration", options)

        if filter_xml is not None:
            if not isinstance(filter_xml, etree._Element):
                if re.search("^<.*>$", filter_xml):
                    filter_xml = etree.XML(filter_xml)
                else:
                    filter_data = None
                    for tag in filter_xml.split("/")[::-1]:
                        filter_data = (
                            E(tag) if filter_data is None else E(tag, filter_data)
                        )
                    filter_xml = filter_data
            # wrap the provided filter with toplevel <configuration> if
            # it does not already have one (not in case of yang model config)
            if (
                filter_xml.tag != "configuration"
                and model is None
                and namespace is None
            ):
                etree.SubElement(rpc, "configuration").append(filter_xml)
            else:
                if model is not None or namespace is not None:
                    if model == "custom" and namespace is None:
                        raise AttributeError(
                            'For "custom" model, ' 'explicitly provide "namespace"'
                        )
                    ns = namespace or (nmspaces.get(model.lower()) + filter_xml.tag)
                    filter_xml.attrib["xmlns"] = ns
                rpc.append(filter_xml)
        transform = self._junos.transform
        if remove_ns is False:
            self._junos.transform = lambda: JXML.strip_namespaces_prefix
        try:
            response = self._junos.execute(rpc, **kwargs)
        finally:
            self._junos.transform = transform
        # in case of model provided top level should be data
        # return response
        if model and filter_xml is None and options.get("format") is not "json":
            response = response.getparent()
            response.tag = "data"
        return response

    # -----------------------------------------------------------------------
    # get
    # -----------------------------------------------------------------------

    def get(self, filter_select=None, ignore_warning=False, **kwargs):
        """
        Retrieve running configuration and device state information using
        <get> rpc

        .. code-block:: python

           dev.rpc.get()
           dev.rpc.get(ignore_warning=True)
           dev.rpc.get(filter_select='bgp') or dev.rpc.get('bgp')
           dev.rpc.get(filter_select='bgp/neighbors')
           dev.rpc.get("/bgp/neighbors/neighbor[neighbor-address='10.10.0.1']"
                       "/timers/state/hold-time")
           dev.rpc.get('mpls', ignore_warning=True)

        :param str filter_select:
          The select attribute will be treated as an XPath expression and
          used to filter the returned data.

        :param ignore_warning: A boolean, string or list of string.
          If the value is True, it will ignore all warnings regardless of the
          warning message. If the value is a string, it will ignore
          warning(s) if the message of each warning matches the string. If
          the value is a list of strings, ignore warning(s) if the message of
          each warning matches at least one of the strings in the list.

          For example::

            dev.rpc.get(ignore_warning=True)
            dev.rpc.get(ignore_warning='vrrp subsystem not running')
            dev.rpc.get(ignore_warning=['vrrp subsystem not running',
                                        'statement not found'])

          .. note::
            When the value of ignore_warning is a string, or list of strings,
            the string is actually used as a case-insensitive regular
            expression pattern. If the string contains only alpha-numeric
            characters, as shown in the above examples, this results in a
            case-insensitive substring match. However, any regular expression
            pattern supported by the re library may be used for more
            complicated match conditions.

        :returns: xml object
        """
        # junos only support filter type to be xpath
        filter_params = {"type": "xpath"}
        if filter_select is not None:
            filter_params["source"] = filter_select
        rpc = E("get", E("filter", filter_params))
        return self._junos.execute(rpc, ignore_warning=ignore_warning, **kwargs)

    # -----------------------------------------------------------------------
    # load_config
    # -----------------------------------------------------------------------

    def load_config(self, contents, ignore_warning=False, **options):
        """
        loads :contents: onto the Junos device, does not commit the change.

        :param ignore_warning: A boolean, string or list of string.
          If the value is True, it will ignore all warnings regardless of the
          warning message. If the value is a string, it will ignore
          warning(s) if the message of each warning matches the string. If
          the value is a list of strings, ignore warning(s) if the message of
          each warning matches at least one of the strings in the list.

          For example::

            dev.rpc.load_config(cnf, ignore_warning=True)
            dev.rpc.load_config(cnf,
                                ignore_warning='vrrp subsystem not running')
            dev.rpc.load_config(cnf,
                                ignore_warning=['vrrp subsystem not running',
                                                'statement not found'])
            dev.rpc.load_config(cnf, ignore_warning='statement not found')

          .. note::
            When the value of ignore_warning is a string, or list of strings,
            the string is actually used as a case-insensitive regular
            expression pattern. If the string contains only alpha-numeric
            characters, as shown in the above examples, this results in a
            case-insensitive substring match. However, any regular expression
            pattern supported by the re library may be used for more
            complicated match conditions.

        :options: is a dictionary of XML attributes to set within the
                  <load-configuration> RPC.

        The :contents: are interpreted by the :options: as follows:

        format='text' and action='set', then :contents: is a string containing
            a series of "set" commands

        format='text', then :contents: is a string containing Junos
            configuration in curly-brace/text format

        format='json', then :contents: is a string containing Junos
            configuration in json format

        url='path', then :contents: is a None

        <otherwise> :contents: is XML structure
        """
        rpc = E("load-configuration", options)

        if contents is None and "url" in options:
            pass
        elif ("action" in options) and (options["action"] == "set"):
            rpc.append(E("configuration-set", contents))
        elif ("action" in options) and (options["action"] == "patch"):
            rpc.append(E("configuration-patch", contents))
        elif ("format" in options) and (options["format"] == "text"):
            rpc.append(E("configuration-text", contents))
        elif ("format" in options) and (options["format"] == "json"):
            rpc.append(E("configuration-json", contents))
        else:
            # otherwise, it's just XML Element
            if contents.tag != "configuration":
                etree.SubElement(rpc, "configuration").append(contents)
            else:
                rpc.append(contents)

        return self._junos.execute(rpc, ignore_warning=ignore_warning)

    # -----------------------------------------------------------------------
    # cli
    # -----------------------------------------------------------------------

    def cli(self, command, format="text", normalize=False):
        rpc = E("command", command)
        if format.lower() in ["text", "json"]:
            rpc.attrib["format"] = format
        return self._junos.execute(rpc, normalize=normalize)

    # -----------------------------------------------------------------------
    # method missing
    # -----------------------------------------------------------------------

    def __getattr__(self, rpc_cmd_name):
        """
        metaprograms a function to execute the :rpc_cmd_name:

        the caller will be passing (*vargs, **kvargs) on
        execution of the meta function; these are the specific
        rpc command arguments(**kvargs) and options bound
        as XML attributes (*vargs)
        """

        rpc_cmd = re.sub("_", "-", rpc_cmd_name)

        def _exec_rpc(*vargs, **kvargs):
            # create the rpc as XML command
            rpc = etree.Element(rpc_cmd)

            # Gather decorator keywords into dec_args and remove from kvargs
            dec_arg_keywords = [
                "dev_timeout",
                "normalize",
                "ignore_warning",
                "filter_xml",
            ]
            dec_args = {}
            for keyword in dec_arg_keywords:
                if keyword in kvargs:
                    dec_args[keyword] = kvargs.pop(keyword)

            # kvargs are the command parameter/values
            if kvargs:
                for arg_name, arg_value in kvargs.items():
                    arg_name = re.sub("_", "-", arg_name)
                    if not isinstance(arg_value, (tuple, list)):
                        arg_value = [arg_value]
                    for a in arg_value:
                        if not isinstance(
                            a,
                            (bool, str, unicode) if sys.version < "3" else (bool, str),
                        ):
                            raise TypeError(
                                "The value %s for argument %s"
                                " is of %s. Argument "
                                "values must be a string, "
                                "boolean, or list/tuple of "
                                "strings and booleans." % (a, arg_name, str(type(a)))
                            )
                        if a is not False:
                            arg = etree.SubElement(rpc, arg_name)
                        if not isinstance(a, bool):
                            arg.text = a

            # vargs[0] is a dict, command options like format='text'
            if vargs:
                for k, v in vargs[0].items():
                    if v is not True:
                        rpc.attrib[k] = v

            # now invoke the command against the
            # associated :junos: device and return
            # the results per :junos:execute()
            return self._junos.execute(rpc, **dec_args)

        # metabind help() and the function name to the :rpc_cmd_name:
        # provided by the caller ... that's about all we can do, yo!

        _exec_rpc.__doc__ = rpc_cmd
        _exec_rpc.__name__ = rpc_cmd_name

        # return the metafunction that the caller will in-turn invoke
        return _exec_rpc

    # -----------------------------------------------------------------------
    # callable
    # -----------------------------------------------------------------------

    def __call__(self, rpc_cmd, **kvargs):
        """
        callable will execute the provided :rpc_cmd: against the
        attached :junos: object and return the RPC response per
        :junos:execute()

        kvargs is simply passed 'as-is' to :junos:execute()
        """
        return self._junos.execute(rpc_cmd, **kvargs)
