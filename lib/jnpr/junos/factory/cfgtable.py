from lxml.builder import E
from jnpr.junos.factory.table import Table
from jnpr.junos import jxml


class CfgTable(Table):

    # -----------------------------------------------------------------------
    # CONSTRUCTOR
    # -----------------------------------------------------------------------

    def __init__(self, dev):
        Table.__init__(self, dev)       # call parent constructor

        self._data_dict = self.DEFINE  # crutch
        self.ITEM_NAME_XPATH = self._data_dict.get('key', 'name')
        self.ITEM_XPATH = self._data_dict['get']
        self.view = self._data_dict.get('view')

    # -----------------------------------------------------------------------
    # PROPERTIES
    # -----------------------------------------------------------------------

    @property
    def required_keys(self):
        """
        return a list of the keys required when invoking :get():
        and :get_keys():
        """
        return self._data_dict.get('required_keys')

    @property
    def keys_required(self):
        """ True/False - if this Table requires keys """
        return self.required_keys is not None

    # -----------------------------------------------------------------------
    # PRIVATE METHODS
    # -----------------------------------------------------------------------

    def _buildxml(self, namesonly=False):
        """
        Return an lxml Element starting with <configuration> and comprised
        of the elements specified in the xpath expression.

        For example, and xpath = 'interfaces/interface' would produce:

         <configuration>
            <interfaces>
              <interface/>
            </interfaces>
          </configuration>

        If :namesonly: is True, then the XML will be encoded only to
        retrieve the XML name keys at the 'end' of the XPath expression.

        This return value can then be passed to dev.rpc.get_config()
        to retrieve the specifc data
        """
        xpath = self._data_dict['get']
        top = E('configuration')
        dot = top
        for name in xpath.split('/'):
            dot.append(E(name))
            dot = dot[0]

        if namesonly is True:
            dot.attrib['recurse'] = 'false'
        return top

    def _grindkey(self, key_xpath, key_value):
        """ returns list of XML elements for key values """
        simple = lambda: [E(key_xpath.replace('_', '-'), key_value)]
        composite = lambda: [E(xp.replace('_', '-'), xv)
                             for xp, xv in zip(key_xpath, key_value)]
        return simple() if isinstance(key_xpath, str) else composite()

    def _encode_requiredkeys(self, get_cmd, kvargs):
        """
        used to encode the required_keys values into the XML get-command.
        each of the required_key=<value> pairs are defined in :kvargs:
        """
        rqkeys = self._data_dict['required_keys']
        for key_name in self.required_keys:
            # create an XML element with the key/value
            key_value = kvargs.get(key_name)
            if key_value is None:
                raise ValueError("Missing required-key: '%s'" % key_name)
            key_xpath = rqkeys[key_name]
            add_keylist_xml = self._grindkey(key_xpath, key_value)

            # now link this item into the XML command, where key_name
            # designates the XML parent element
            dot = get_cmd.find('.//' + key_name.replace('_', '-'))
            if dot is None:
                raise RuntimeError(
                    "Unable to find parent XML for key: '%s'" %
                    key_name)
            for _at, _add in enumerate(add_keylist_xml):
                dot.insert(_at, _add)

    def _encode_namekey(self, get_cmd, dot, namekey_value):
        """
        encodes the specific namekey_value into the get command so that the
        returned XML configuration is the complete hierarchy of data.
        """
        namekey_xpath = self._data_dict.get('key', 'name')
        keylist_xml = self._grindkey(namekey_xpath, namekey_value)
        for _add in keylist_xml:
            dot.append(_add)

    def _encode_getfields(self, get_cmd, dot):
        for field_xpath in self._data_dict['get_fields']:
            dot.append(E(field_xpath))

    def _keyspec(self):
        """ returns tuple (keyname-xpath, item-xpath) """
        return (self._data_dict.get('key', 'name'), self._data_dict['get'])

    # -------------------------------------------------------------------------
    # get - retrieve Table data
    # -------------------------------------------------------------------------

    def get(self, *vargs, **kvargs):
        """
        Retrieve configuration data for this table.  By default all child
        keys of the table are loaded.  This behavior can be overridden by
        with kvargs['nameonly']=True

        :param str vargs[0]: identifies a unique item in the table,
          same as calling with :kvargs['key']: value

        :param str namesonly:
          *OPTIONAL* True/False*, when set to True will cause only the
          the name-keys to be retrieved.

        :param str key:
          *OPTIONAL* identifies a unique item in the table

        :param dict options:
          *OPTIONAL* options to pass to get-configuration.  By default
          {'inherit': 'inherit', 'groups': 'groups'} is sent.
        """
        if self.keys_required is True and not len(kvargs):
            raise ValueError(
                "This table has required-keys\n",
                self.required_keys)

        self._clearkeys()

        # determine if we need to get only the names of keys, or all of the
        # hierarchical data from the config.  The caller can explicitly set
        # :namesonly: in the call.

        if 'namesonly' in kvargs:
            namesonly = kvargs.get('namesonly')
        else:
            namesonly = False

        get_cmd = self._buildxml(namesonly=namesonly)

        # if this table requires additional keys, for the hierarchical
        # use-cases then make sure these are provided by the caller. Then
        # encode them into the 'get-cmd' XML

        if self.keys_required is True:
            self._encode_requiredkeys(get_cmd, kvargs)

        try:
            # see if the caller provided a named item.  this must
            # be an actual name of a thing, and not an index number.
            # ... at least for now ...
            named_item = kvargs.get('key') or vargs[0]
            dot = get_cmd.find(self._data_dict['get'])
            self._encode_namekey(get_cmd, dot, named_item)

            if 'get_fields' in self._data_dict:
                self._encode_getfields(get_cmd, dot)

        except:
            # caller not requesting a specific table item
            pass

        # Check for options in get
        if 'options' in kvargs:
            options = kvargs.get('options') or {}
        else:
            options = jxml.INHERIT_GROUPS

        # for debug purposes
        self._get_cmd = get_cmd
        self._get_opt = options

        # retrieve the XML configuration
        self.xml = self.RPC.get_config(get_cmd, options=options)

        # return self for call-chaining, yo!
        return self
