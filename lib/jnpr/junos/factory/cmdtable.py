import re
import copy
# https://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts

# local
from jnpr.junos.exception import RpcError
from jnpr.junos.utils.start_shell import StartShell
from jnpr.junos.factory.state_machine import StateMachine
from jnpr.junos.factory.to_json import TableJSONEncoder

# stdlib
from inspect import isclass
from lxml import etree

import json

from jinja2 import Template


class CMDTable(object):

    def __init__(self, dev=None, output=None, path=None):
        """
        :dev: Device instance
        :output: string blob of the command output
        :path: file path to XML, to be used rather than :dev:
        """
        self._dev = dev
        self.xml = output
        self.view = None
        self.ITEM_FILTER = 'name'
        self._key_list = []
        self._path = path
        self._parser = None
        self.output = None

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    def get(self, *vargs, **kvargs):
        """
        Retrieve the XML (string blob under <output> tag of table data from the
        Device instance and returns back the Table instance - for call-chaining
        purposes.

        If the Table was created with a :path: rather than a Device,
        then this method will load the string blob from that file.  In this
        case, the \*vargs, and \**kvargs are not used.

        ALIAS: __call__

        :vargs:
          [0] is the table :arg_key: value.  This is used so that
          the caller can retrieve just one item from the table without
          having to know the Junos RPC argument.

        :kvargs:
          these are the name/value pairs relating to the specific Junos
          command attached to the table.  For example, if the command
          is 'show ithrottle id {{ id }}', there is a parameter 'id'.
          Any valid command argument can be passed to :kvargs: to further filter
          the results of the :get(): operation.  neato!

        NOTES:
          If you need to create a 'stub' for unit-testing
          purposes, you want to create a subclass of your table and
          overload this methods.
        """
        self._clearkeys()

        if self._path is not None:
            # for loading from local file-path
            with open(self._path, 'r') as fp:
                self.data = fp.read().strip()
            if self.data.startswith('<output>') and self.data.endswith(
                    '</output>'):
                self.data = etree.fromstring(self.data).text
            sm = StateMachine(self)
            self.output = sm.parse(self.data.splitlines())
            return self

        if 'target' in kvargs:
            self.TARGET = kvargs['target']

        if 'key' in kvargs:
            self.KEY = kvargs['key']

        if 'key_items' in kvargs:
            self.KEY_ITEMS = kvargs['key_items']

        if 'filters' in kvargs:
            self.VIEW.FILTERS = [kvargs['filters']] if isinstance(kvargs[
                                                                   'filters'],
                                                                str) else \
                kvargs['filters']

        if 'args' in kvargs and isinstance(kvargs['args'], dict):
            self.CMD_ARGS.update(kvargs['args'])

        if len(self.CMD_ARGS) > 0:
            self.GET_CMD = Template(self.GET_CMD).render(**self.CMD_ARGS)

        # execute the Junos RPC to retrieve the table
        if hasattr(self, 'TARGET'):
            if self.TARGET is None:
                raise ValueError('"target" value not provided')
            rpc_args = {'target': self.TARGET, 'command': self.GET_CMD,
                        'timeout': '0'}
            try:
                self.xml = getattr(self.RPC, 'request_pfe_execute')(**rpc_args)
                self.data = self.xml.text
                ver_info = self._dev.facts.get('version_info')
                if ver_info and ver_info.major[0] <= 15:
                    # Junos <=15.x output has output something like below
                    #
                    # <rpc-reply>
                    # <output>
                    # SENT: Ukern command: show memory
                    # GOT:
                    # GOT: ID      Base      Total(b)       Free(b)     Used(b)
                    # GOT: --  --------     ---------     ---------   ---------
                    # GOT:  0  44e72078    1882774284    1689527364   193246920
                    # GOT:  1  b51ffb88      67108860      57651900     9456960
                    # GOT:  2  bcdfffe0      52428784      52428784           0
                    # GOT:  3  b91ffb88      62914556      62914556           0
                    # LOCAL: End of file
                    # </output>
                    # </rpc-reply>
                    # hence need to do cleanup
                    self.data = self.data.replace("GOT: ", "")
            except RpcError:
                with StartShell(self.D) as ss:
                    ret = ss.run('cprod -A %s -c "%s"' % (self.TARGET,
                                                          self.GET_CMD))
                    if ret[0]:
                        self.data = ret[1]
        else:
            self.xml = self.RPC.cli(self.GET_CMD)
            self.data = self.xml.text

        # state machine
        sm = StateMachine(self)

        self.output = sm.parse(self.data.splitlines())

        # returning self for call-chaining purposes, yo!
        return self

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------

    @property
    def D(self):
        """ the Device instance """
        return self._dev

    @property
    def CLI(self):
        """ the Device.cli instance """
        return self.D.cli

    @property
    def RPC(self):
        """ the Device.rpc instance """
        return self.D.rpc

    @property
    def view(self):
        """ returns the current view assigned to this table """
        return self._view

    @view.setter
    def view(self, cls):
        """ assigns a new view to the table """
        if cls is None:
            self._view = None
            return

        if not isclass(cls):
            raise ValueError("Must be given RunstatView class")

        self._view = cls

    @property
    def hostname(self):
        return self.D.hostname

    @property
    def key_list(self):
        """ the list of keys, as property for caching """
        return self._key_list

    # -------------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------------

    def _assert_data(self):
        if self.data is None:
            raise RuntimeError("Table is empty, use get()")

    def _clearkeys(self):
        self._key_list = []

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    # ------------------------------------------------------------------------
    # keys
    # ------------------------------------------------------------------------

    def _keys(self):
        """ return a list of data item keys from the data string """

        return self.output.keys()

    def keys(self):
        # if the key_list has been cached, then use it
        if len(self.key_list):
            return self.key_list

        # otherwise, build the list of keys into the cache
        self._key_list = self._keys()
        return self._key_list

    # ------------------------------------------------------------------------
    # values
    # ------------------------------------------------------------------------

    def values(self):
        """ returns list of table entry items() """

        self._assert_data()
        return self.output.values()

    # ------------------------------------------------------------------------
    # items
    # ------------------------------------------------------------------------

    def items(self):
        """ returns list of tuple(name,values) for each table entry """
        return self.output.items()

    def to_json(self):
        """
        :returns: JSON encoded string of entire Table contents
        """
        return json.dumps(self, cls=TableJSONEncoder)

    # -------------------------------------------------------------------------
    # OVERLOADS
    # -------------------------------------------------------------------------

    __call__ = get

    def __repr__(self):
        cls_name = self.__class__.__name__
        source = self.D.hostname if self.D is not None else self._path

        if self.data is None:
            return "%s:%s - Table empty" % (cls_name, source)
        else:
            n_items = len(self.keys())
            return "%s:%s: %s items" % (cls_name, source, n_items)

    def __len__(self):
        self._assert_data()
        return len(self.keys())

    def __iter__(self):
        """ iterate over each time in the table """
        self._assert_data()

        for key, value in self.output.items():
            yield key, value

    def __getitem__(self, value):
        """
        returns a table item. If a table view is set (should be by default)
        then the item will be converted to the view upon return.  if there is
        no table view, then the XML object will be returned.

        :value:
          for <string>, this will perform a select based on key-name
          for <tuple>, this will perform a select based on compsite key-name
          for <int>, this will perform a select based by position, like <list>
            [0] is the first item
            [-1] is the last item
          when it is a <slice> then this will return a <list> of View widgets
        """
        self._assert_data()
        return self.output[value]

    def __contains__(self, key):
        """ membership for use with 'in' """
        return bool(key in self.keys())
