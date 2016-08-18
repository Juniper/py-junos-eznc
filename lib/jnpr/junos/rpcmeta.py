import re
from lxml import etree
from lxml.builder import E


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

    def get_config(self, filter_xml=None, options={}):
        """
        retrieve configuration from the Junos device

        :filter_xml: fully XML formatted tag which defines what to retrieve,
                     when omitted the entire configuration is returned;
                     the following returns the device host-name configured with "set system host-name":

        config = dev.rpc.get_config(filter_xml=etree.XML('<configuration><system><host-name/></system></configuration>'))

        :options: is a dictionary of XML attributes to set within the <get-configuration> RPC;
                  the following returns the device host-name either configured with "set system host-name"
                  and if unconfigured, the value inherited from apply-group re0|re1, typical for multi-RE systems:

        config = dev.rpc.get_config(filter_xml=etree.XML('<configuration><system><host-name/></system></configuration>'), 
                 options={'database':'committed','inherit':'inherit'})

        """
        rpc = E('get-configuration', options)

        if filter_xml is not None:
            # wrap the provided filter with toplevel <configuration> if
            # it does not already have one
            cfg_tag = 'configuration'
            at_here = rpc if cfg_tag == filter_xml.tag else E(cfg_tag)
            at_here.append(filter_xml)
            if at_here is not rpc: rpc.append(at_here)

        return self._junos.execute(rpc)

    # -----------------------------------------------------------------------
    # load_config
    # -----------------------------------------------------------------------

    def load_config(self, contents, **options):
        """
        loads :contents: onto the Junos device, does not commit the change.

        :options: is a dictionary of XML attributes to set within the <load-configuration> RPC.

        The :contents: are interpreted by the :options: as follows:

        format='text' and action='set', then :contents: is a string containing a series of "set" commands

        format='text', then :contents: is a string containing Junos configuration in curly-brace/text format

        format='json', then :contents: is a string containing Junos configuration in json format

        <otherwise> :contents: is XML structure
        """
        rpc = E('load-configuration', options)

        if ('action' in options) and (options['action'] == 'set'):
            rpc.append(E('configuration-set', contents))
        elif ('format' in options) and (options['format'] == 'text'):
            rpc.append(E('configuration-text', contents))
        elif ('format' in options) and (options['format'] == 'json'):
            rpc.append(E('configuration-json', contents))
        else:
            # otherwise, it's just XML Element
            if contents.tag != 'configuration':
                etree.SubElement(rpc, 'configuration').append(contents)
            else:
                rpc.append(contents)

        return self._junos.execute(rpc)

    # -----------------------------------------------------------------------
    # cli
    # -----------------------------------------------------------------------

    def cli(self, command, format='text'):
        rpc = E('command', command)
        if format.lower() in ['text', 'json']:
            rpc.attrib['format'] = format
        return self._junos.execute(rpc)

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

        rpc_cmd = re.sub('_', '-', rpc_cmd_name)

        def _exec_rpc(*vargs, **kvargs):
            # create the rpc as XML command
            rpc = etree.Element(rpc_cmd)

            # kvargs are the command parameter/values
            if kvargs:
                for arg_name, arg_value in kvargs.items():
                    if arg_name not in ['dev_timeout', 'normalize']:
                        arg_name = re.sub('_', '-', arg_name)
                        if isinstance(arg_value, (tuple, list)):
                            for a in arg_value:
                                arg = etree.SubElement(rpc, arg_name)
                                if a is not True:
                                    arg.text = a
                        else:
                            arg = etree.SubElement(rpc, arg_name)
                            if arg_value is not True:
                                arg.text = arg_value

            # vargs[0] is a dict, command options like format='text'
            if vargs:
                for k, v in vargs[0].items():
                    if v is not True:
                        rpc.attrib[k] = v

            # gather any decorator keywords
            timeout = kvargs.get('dev_timeout')
            normalize = kvargs.get('normalize')

            dec_args = {}

            if timeout is not None:
                dec_args['dev_timeout'] = timeout
            if normalize is not None:
                dec_args['normalize'] = normalize

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
