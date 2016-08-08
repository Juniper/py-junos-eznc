from copy import deepcopy
import re

from lxml import etree
from lxml.builder import E
from jnpr.junos.factory.table import Table
from jnpr.junos import jxml
from jnpr.junos.utils.config import Config


class CfgTable(Table):

    __isfrozen = False

    # -----------------------------------------------------------------------
    # CONSTRUCTOR
    # -----------------------------------------------------------------------
    def __init__(self, dev=None, xml=None, path=None, mode=None):
        Table.__init__(self, dev, xml, path)       # call parent constructor

        self._init_get()
        self._data_dict = self.DEFINE  # crutch
        self.ITEM_NAME_XPATH = self._data_dict.get('key', 'name')
        self.view = self._data_dict.get('view')
        self._options = self._data_dict.get('options')
        self.mode = mode
        if 'set' in self._data_dict:
            Config.__init__(self, dev, mode)    # call parent constructor

            self._init_set()
            if self._view:
                self.fields = self._view.FIELDS.copy()
            else:
                raise ValueError(
                    "%s set table view is not defined.\n"
                    % (self.__class__.__name__)
                )
            if 'key-field' in self._data_dict:
                key_name = self._data_dict.get('key-field', None)
                if isinstance(key_name, list):
                    self.key_field = key_name
                elif isinstance(key_name, str):
                    self.key_field = [key_name]
                else:
                    raise TypeError(
                        "Key-field %s is of invalid type %s.\n"
                        % (key_name, type(key_name))
                    )
            else:
                raise ValueError(
                    "Table should have key-field attribute defined\n"
                )
            self._type = 'set'
            self._init_field()
        else:
            self._type = 'get'
        self.ITEM_XPATH = self._data_dict[self._type]

        # no new attributes.
        self._freeze()

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
    def _init_get(self):
        self._get_xpath = None

        # for debug purposes
        self._get_cmd = None
        self._get_opt = None

    def _init_set(self):
        self._insert_node = None

        # lxml object of configuration xml
        self._config_xml_req = None

        # To check if field value is set.
        self._is_field_set = False

        # for debug purposes
        self._load_rsp = None
        self._commit_rsp = None

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
        xpath = self._data_dict[self._type]
        self._get_xpath = '//configuration/' + xpath
        top = E('configuration')
        dot = top
        for name in xpath.split('/'):
            dot.append(E(name))
            dot = dot[0]

        if namesonly is True:
            dot.attrib['recurse'] = 'false'
        return top

    def _build_config_xml(self, top):
        """
        used to encode the field values into the configuration XML
        for set table,each of the field=<value> pairs are defined by user:
        """
        for field_name, opt in self.fields.items():
            dot = top
            # create an XML element with the key/value
            field_value = getattr(self, field_name, None)
            # If field value is not set ignore it
            if field_value is None:
                continue

            if isinstance(field_value, (list, tuple, set)):
                [self._validate_value(field_name, v, opt) for v in field_value]
            else:
                self._validate_value(field_name, field_value, opt)

            field_dict = self.fields[field_name]

            if 'group' in field_dict:
                group_xpath = self._view.GROUPS[field_dict['group']]
                dot = self._encode_xpath(top, group_xpath.split('/'))

            lxpath = field_dict['xpath'].split('/')
            if len(lxpath) > 1:
                dot = self._encode_xpath(top, lxpath[0:len(lxpath) - 1])

            add_field = self._grindfield(lxpath[-1], field_value)
            for _add in add_field:
                if len(_add.attrib) > 0:
                    for i in dot.getiterator():
                        if i.tag == _add.tag:
                            i.attrib.update(_add.attrib)
                            break
                    else:
                        dot.append(_add)
                elif field_name in self.key_field:
                    dot.insert(0, _add)
                else:
                    dot.append(_add)

    def _validate_value(self, field_name, value, opt):
        """
        Validate value set for field against the constraints and
        data type check define in yml table/view defination.

        :param field_name: Name of field as mentioned in yaml table/view
        :param value: Value set by user for field_name.
        :param opt: Dictionary of data type and constraint check.
        :return:
        """
        def _get_field_type(ftype):
            ft = {
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
            }.get(ftype, None)

            if ft is None:
                raise TypeError("Unsupported type %s\n" % (ftype))
            return ft

        def _validate_enum_value(field_name, value, enum_value):
            if isinstance(enum_value, list):
                if value not in enum_value:
                    raise ValueError('Invalid value %s assigned '
                                     'to field %s' % (value, field_name))
            elif isinstance(enum_value, str):
                if not value == enum_value:
                    raise ValueError('Invalid value %s assigned '
                                     'to field %s' % (value, field_name))
            else:
                raise TypeError('Value of enum should '
                                'be either a string or list of strings.\n')

        def _validate_type(field_name, value, opt):
            if isinstance(opt['type'], dict):
                if 'enum' in opt['type']:
                    _validate_enum_value(field_name,
                                         value, opt['type']['enum'])
                else:
                    # More user defined type check can be added in future.
                    # raise execption for now.
                    raise TypeError("Unsupported type %s\n" % (opt['type']))

            elif isinstance(opt['type'], str):
                field_type = _get_field_type(opt['type'])
                if not isinstance(value, field_type):
                    raise TypeError(
                        'Invalid value %s asigned to field %s,'
                        ' value should be of type %s\n'
                        % (value, field_name, field_type)
                    )
            else:
                raise TypeError(
                    'Invalid value %s, should be either of'
                    ' type string or dictionary.\n' % (opt['type'])
                )

        def _validate_min_max_value(field_name, value, opt):
            if isinstance(value, (int, float)):
                if value < opt['minValue'] or value > opt['maxValue']:
                    raise ValueError(
                        'Invalid value %s assigned '
                        'to field %s.\n' % (value, field_name)
                    )
            elif isinstance(value, str):
                if len(value) < opt['minValue'] or \
                        len(value) > opt['maxValue']:
                    raise ValueError(
                        'Invalid value %s assigned '
                        'to field %s.\n' % (value, field_name)
                    )

        if isinstance(value, dict) and 'operation' in value:
            # in case user want to pass operation attr for ex:
            # <unit operation="delete"/>
            pass
        elif isinstance(value, (list, tuple, dict, set)):
            raise ValueError("%s value is invalid %s\n" % (field_name, value))
        else:
            if 'type' in opt:
                _validate_type(field_name, value, opt)
            if ('minValue' or 'maxValue') in opt:
                _validate_min_max_value(field_name, value, opt)

    def _grindkey(self, key_xpath, key_value):
        """ returns list of XML elements for key values """
        simple = lambda: [E(key_xpath.replace('_', '-'), key_value)]
        composite = lambda: [E(xp.replace('_', '-'), xv)
                             for xp, xv in zip(key_xpath, key_value)]
        return simple() if isinstance(key_xpath, str) else composite()

    def _grindxpath(self, key_xpath, key_value):
        """ returns xpath elements for key values """
        simple = lambda: "[{0}='{1}']".format(
            key_xpath.replace('_', '-'),
            key_value
        )
        composite = lambda: "[{0}]".format(' and '.join(
                            ["{0}='{1}'".format(xp.replace('_', '-'), xv)
                                for xp, xv in zip(key_xpath, key_value)]))
        return simple() if isinstance(key_xpath, str) else composite()

    def _grindfield(self, xpath, value):
        """ returns list of xml elements for field name-value pairs """
        lst = []
        if isinstance(value, (list, tuple, set)):
            for v in value:
                lst.append(E(xpath.replace('_', '-'), str(v)))
        elif isinstance(value, bool):
            if value is True:
                lst.append(E(xpath.replace('_', '-')))
            elif value is False:
                lst.append(E(xpath.replace('_', '-'), {'operation': 'delete'}))
        elif isinstance(value, dict) and 'operation' in value:
            lst.append(E(xpath.replace('_', '-'), value))
        else:
            lst.append(E(xpath.replace('_', '-'), str(value)))
        return lst

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
                raise ValueError("Missing required-key: '%s'" % (key_name))
            key_xpath = rqkeys[key_name]
            add_keylist_xml = self._grindkey(key_xpath, key_value)

            # now link this item into the XML command, where key_name
            # designates the XML parent element
            key_name = key_name.replace('_', '-')
            dot = get_cmd.find('.//' + key_name)
            if dot is None:
                raise RuntimeError(
                    "Unable to find parent XML for key: '%s'" %
                    (key_name))
            for _at, _add in enumerate(add_keylist_xml):
                dot.insert(_at, _add)

            # Add required key values to _get_xpath
            xid = re.search(r"\b{0}\b".format(key_name),
                            self._get_xpath).start() + len(key_name)

            self._get_xpath = self._get_xpath[:xid] + \
                self._grindxpath(key_xpath, key_value) + \
                self._get_xpath[xid:]

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

    def _encode_xpath(self, top, lst):
        """
        Create xml element hierarchy for given field. Return container
        node to which field and its value will appended as child elements.
        """
        dot = top
        for index in range(1, len(lst) + 1):
            xp = '/'.join(lst[0:index])
            if not len(top.xpath(xp)):
                dot.append(E(lst[index - 1]))
            dot = dot.find(lst[index - 1])
        return dot

    def _keyspec(self):
        """ returns tuple (keyname-xpath, item-xpath) """
        return (self._data_dict.get('key', 'name'),
                self._data_dict[self._type])

    def _init_field(self):
        """
        Initialize fields of set table to it's default value
        (if mentioned in yml Table/View) else set to None.
        """
        for fname, opt in self.fields.items():
            self.__dict__[fname] = opt['default'] \
                if 'default' in opt else None

    def _mandatory_check(self):
        """ Mandatory checks for set table/view  """
        for key in self.key_field:
            value = getattr(self, key)
            if value is None:
                raise ValueError("%s key-field value is not set.\n" % (key))

    def _freeze(self):
        """
        Freeze class object so that user cannot add new attributes (fields).
        """
        self.__isfrozen = True

    def _unfreeze(self):
        """
        Unfreeze class object, should be called from within class only.
        """
        self.__isfrozen = False

    # ----------------------------------------------------------------------
    # reset - Assign 'set' Table field values to default or None
    # ----------------------------------------------------------------------
    def reset(self):
        """
        Initialize fields of set table to it's default value
        (if mentioned in Table/View) else set to None.
        """
        return self._init_field()

    # ----------------------------------------------------------------------
    # get_table_xml - retrieve lxml configuration object for set table
    # ----------------------------------------------------------------------
    def get_table_xml(self):
        """
        It returns lxml object of configuration xml that is generated
        from table data (field=value) pairs. To get a valid xml this
        method should be used after append() is called.
        """
        return self._config_xml_req

    # ----------------------------------------------------------------------
    # append - append Table data to lxml configuration object
    # ----------------------------------------------------------------------
    def append(self):
        """
        It creates lxml nodes with field name as xml tag and its value
        given by user as text of xml node. The generated xml nodes are
        appended to configuration xml at appropriate hierarchy.

        .. warning::
            xml node that are appended cannot be changed later hence
            care should be taken to assign correct value to table fields
            before calling append.
        """

        # mandatory check for 'set' table fields
        self._mandatory_check()

        set_cmd = self._buildxml()
        top = set_cmd.find(self._data_dict[self._type])
        self._build_config_xml(top)
        if self._config_xml_req is None:
            self._config_xml_req = set_cmd
            self._insert_node = top.getparent()
        else:
            self._insert_node.extend(top.getparent())

        self.reset()                 # Reset field values
        self._is_field_set = False

    # ----------------------------------------------------------------------
    # get - retrieve Table data
    # ----------------------------------------------------------------------

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
        if self._lxml is not None:
            return self

        if self._path is not None:
            # for loading from local file-path
            self.xml = etree.parse(self._path).getroot()
            return self

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
            dot = get_cmd.find(self._data_dict[self._type])
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
            if self._options is not None:
                options = self._options
            else:
                options = jxml.INHERIT_GROUPS

        # for debug purposes
        self._get_cmd = get_cmd
        self._get_opt = options

        # retrieve the XML configuration
        # Check to see if running on box
        if self._dev.ON_JUNOS:
            try:
                from junos import Junos_Configuration

                # If part of commit script use the context
                if Junos_Configuration is not None:
                    # Convert the onbox XML to ncclient reply
                    config = jxml.conf_transform(
                        deepcopy(jxml.cscript_conf(Junos_Configuration)),
                        subSelectionXPath=self._get_xpath
                    )
                    self.xml = config.getroot()
                else:
                    self.xml = self.RPC.get_config(get_cmd, options=options)
            # If onbox import missing fallback to RPC - possibly raise
            # exception in future
            except ImportError:
                self.xml = self.RPC.get_config(get_cmd, options=options)
        else:
            self.xml = self.RPC.get_config(get_cmd, options=options)

        # return self for call-chaining, yo!
        return self

    # -----------------------------------------------------------------------
    # set - configure Table data in running configuration.
    # -----------------------------------------------------------------------

    def set(self, **kvargs):
        """
        Load configuration data in running db.
        It performs following operation in sequence.

        * lock(): Locks candidate configuration db.
        * load(): Load structured configuration xml in candidate db.
        * commit(): Commit configuration to runnning db.
        * unlock(): Unlock candidate db.

        This method should be used after append() is called to
        get the desired results.

        :param bool overwrite:
          Determines if the contents completely replace the existing
          configuration.  Default is ``False``.

        :param bool merge:
          If set to ``True`` will set the load-config action to merge.
          the default load-config action is 'replace'

        :param str comment: If provided logs this comment with the commit.

        :param int confirm: If provided activates confirm safeguard with
                            provided value as timeout (minutes).

        :param int timeout: If provided the command will wait for completion
                            using the provided value as timeout (seconds).
                            By default the device timeout is used.

        :param bool sync: On dual control plane systems, requests that
                            the candidate configuration on one control plane
                            be copied to the other control plane, checked for
                            correct syntax, and committed on both Routing
                            Engines.

        :param bool force_sync: On dual control plane systems, forces the
                            candidate configuration on one control plane
                            to be copied to the other control plane.

        :param bool full: When true requires all the daemons to check and
                          evaluate the new configuration.

        :param bool detail: When true return commit detail as XML

        :returns: Class object:

        :raises: ConfigLoadError:
                    When errors detected while loading
                    configuration. You can use the Exception errs
                    variable to identify the specific problems

                CommitError:
                    When errors detected in candidate configuration.
                    You can use the Exception errs variable
                    to identify the specific problems

                RuntimeError:
                    If field value is set and append() is not
                    invoked before calling this method, it will
                    raise an exception with appropriate error
                    message.

        .. warning::
            If the function does not receive a reply prior to the timeout
            a RpcTimeoutError will be raised.  It is possible the commit
            was successful.  Manual verification may be required.
        """
        if self._is_field_set:
            raise RuntimeError("Field value is changed, append() "
                               "must be called before set()")

        self.lock()

        try:
            # Invoke config class load() api, with xml object.
            self._load_rsp = super(CfgTable, self).load(self._config_xml_req,
                                                        **kvargs)
            self._commit_rsp = self.commit(**kvargs)
        finally:
            self.unlock()

        return self

    # -----------------------------------------------------------------------
    # OVERLOADS
    # -----------------------------------------------------------------------

    def __setitem__(self, t_field, value):
        """
        implements []= to set Field value
        """
        if t_field in self.fields:
            # pass 'up' to standard setattr method
            self.__setattr__(t_field, value)
        else:
            raise ValueError("Unknown field: %s" % (t_field))

    def __setattr__(self, attribute, value):
        if self.__isfrozen and not hasattr(self, attribute):
            raise ValueError("Unknown field: %s" % (attribute))
        else:
            # pass 'up' to standard setattr method
            object.__setattr__(self, attribute, value)
            if hasattr(self, 'fields') and attribute in self.fields:
                object.__setattr__(self, '_is_field_set', True)

    def __enter__(self):
        return super(CfgTable, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return super(CfgTable, self).__exit__(exc_type, exc_val, exc_tb)

    # -----------------------------------------------------------------------
    # load - configure Table data in candidate configuration.
    # -----------------------------------------------------------------------

    def load(self, **kvargs):
        """
        Load configuration xml having table data (field=value)
        in candidate db.
        This method should be used after append() is called to
        get the desired results.

        :param bool overwrite:
          Determines if the contents completely replace the existing
          configuration.  Default is ``False``.

        :param bool merge:
          If set to ``True`` will set the load-config action to merge.
          the default load-config action is 'replace'

        :returns: Class object.

        :raises: ConfigLoadError:
                    When errors detected while loading
                    configuration. You can use the Exception errs
                    variable to identify the specific problems
                 RuntimeError:
                    If field value is set and append() is not
                    invoked before calling this method, it will
                    raise an exception with appropriate error
                    message.
        """
        if self._is_field_set:
            raise RuntimeError("Field value is changed, append() "
                               "must be called before load()")

        # pass up to config class load() api, with xml object as vargs[0].
        self._load_rsp = super(CfgTable, self).load(self._config_xml_req,
                                                    **kvargs)
        return self
