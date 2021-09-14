from copy import deepcopy
import logging

# 3rd-party
from lxml import etree
from lxml.builder import E

# local
from jnpr.junos.factory.table import Table
from jnpr.junos.jxml import remove_namespaces, remove_namespaces_and_spaces
from jnpr.junos.decorators import checkSAXParserDecorator

logger = logging.getLogger("jnpr.junos.factory.optable")


class OpTable(Table):

    # -------------------------------------------------------------------------
    # PUBLIC METHODS
    # -------------------------------------------------------------------------

    @checkSAXParserDecorator
    def get(self, *vargs, **kvargs):
        """
        Retrieve the XML table data from the Device instance and
        returns back the Table instance - for call-chaining purposes.

        If the Table was created with a :path: rather than a Device,
        then this method will load the XML from that file.  In this
        case, the \*vargs, and \**kvargs are not used.

        ALIAS: __call__

        :vargs:
          [0] is the table :arg_key: value.  This is used so that
          the caller can retrieve just one item from the table without
          having to know the Junos RPC argument.

        :kvargs:
          these are the name/value pairs relating to the specific Junos
          XML command attached to the table.  For example, if the RPC
          is 'get-route-information', there are parameters such as
          'table' and 'destination'.  Any valid RPC argument can be
          passed to :kvargs: to further filter the results of the :get():
          operation.  neato!

        NOTES:
          If you need to create a 'stub' for unit-testing
          purposes, you want to create a subclass of your table and
          overload this methods.
        """
        self._clearkeys()

        if self._path is not None:
            # for loading from local file-path
            self.xml = remove_namespaces(etree.parse(self._path).getroot())
            return self

        if self._lxml is not None:
            return self

        argkey = vargs[0] if len(vargs) else None

        rpc_args = {}

        if self._use_filter:
            try:
                filter_xml = generate_sax_parser_input(self)
                rpc_args["filter_xml"] = filter_xml
            except Exception as ex:
                logger.debug("Not able to create SAX parser input due to " "'%s'" % ex)

        self.D.transform = lambda: remove_namespaces_and_spaces
        rpc_args.update(self.GET_ARGS)  # copy default args
        # saltstack get_table pass args as named keyword
        if "args" in kvargs and isinstance(kvargs["args"], dict):
            rpc_args.update(kvargs.pop("args"))
        rpc_args.update(kvargs)  # copy caller provided args

        if hasattr(self, "GET_KEY") and argkey is not None:
            rpc_args.update({self.GET_KEY: argkey})

        # execute the Junos RPC to retrieve the table
        self.xml = getattr(self.RPC, self.GET_RPC)(**rpc_args)

        # returning self for call-chaining purposes, yo!
        return self


def generate_sax_parser_input(obj):
    """
    Used to generate xml object from Table/view to be used in SAX parsing
    Args:
    obj: self object which contains table/view details

    Returns: lxml etree object to be used as sax parser input

    """
    item_tags = []
    if "/" in obj.ITEM_XPATH:
        item_tags = obj.ITEM_XPATH.split("/")
        parser_ingest = E(item_tags.pop(-1), E(obj.ITEM_NAME_XPATH))
    else:
        parser_ingest = E(obj.ITEM_XPATH, E(obj.ITEM_NAME_XPATH))
    local_field_dict = deepcopy(obj.VIEW.FIELDS)
    # first make element out of group fields
    if obj.VIEW.GROUPS:
        for group, group_xpath in obj.VIEW.GROUPS.items():
            # need to pop out group items so that it wont be reused with fields
            group_field_dict = {
                k: local_field_dict.pop(k)
                for k, v in obj.VIEW.FIELDS.items()
                if v.get("group") == group
            }
            group_ele = E(group_xpath)
            for key, val in group_field_dict.items():
                group_ele.append(E(val.get("xpath")))
            parser_ingest.append(group_ele)
    for i, item in enumerate(local_field_dict.items()):
        # i is the index and item will be taple of field key and value
        field_dict = item[1]
        if "table" in field_dict:
            # handle nested table/view
            child_table = field_dict.get("table")
            parser_ingest.insert(i + 1, generate_sax_parser_input(child_table))
        else:
            xpath = field_dict.get("xpath")
            # xpath can be multi level, for ex traffic-statistics/input-pps
            # going in reverse order, for fields example.
            # split xpath in 2 part, search for first part xpath, if exists, append later
            # else continue, and finally add full xpath to parent
            # min-delay: probe-test-global-results/probe-test-generic-results/probe-test-rtt/probe-summary-results/min-delay
            # max-delay: probe-test-global-results/probe-test-generic-results/probe-test-rtt/probe-summary-results/max-delay
            # avg-delay: probe-test-global-results/probe-test-generic-results/probe-test-rtt/probe-summary-results/avg-delay
            # positive-rtt-jitter: probe-test-global-results/probe-test-generic-results/probe-test-positive-round-trip-jitter/probe-summary-results/avg-delay
            # loss-percentage: probe-test-global-results/probe-test-generic-results/loss-percentage
            # current-min-delay: probe-last-test-results/probe-test-generic-results/probe-test-rtt/probe-summary-results/min-delay
            # current-max-delay: probe-last-test-results/probe-test-generic-results/probe-test-rtt/probe-summary-results/max-delay
            # current-avg-delay: probe-last-test-results/probe-test-generic-results/probe-test-rtt/probe-summary-results/avg-delay
            # current-positive-rtt-jitter: probe-last-test-results/probe-test-generic-results/probe-test-positive-round-trip-jitter/probe-summary-results/avg-delay
            # current-loss-percentage: probe-last-test-results/probe-test-generic-results/loss-percentage
            if "/" in xpath:
                tags = xpath.split("/")
                tags_len = len(tags)
                local_elem_to_add = E(tags[-1])
                for i in range(tags_len, 0, -1):
                    xpath = "/".join(tags[:i])
                    local_obj = parser_ingest
                    elem_exists = local_obj.xpath(xpath)
                    if elem_exists:
                        xpath_exists = elem_exists[0]
                        xpath_exists.insert(1, local_elem_to_add)
                        break
                    if local_elem_to_add.tag != tags[i - 1]:
                        local_elem_to_add = E(tags[i - 1], local_elem_to_add)
                else:
                    parser_ingest.insert(1, local_elem_to_add)
            else:
                parser_ingest.insert(i + 1, E(xpath))
    # cases where item is something like
    # item: task-memory-malloc-usage-report/task-malloc-list/task-malloc
    # created filter from last item task-malloc
    # Now add all the tags if present
    for item_tag in item_tags[::-1]:
        parser_ingest = E(item_tag, parser_ingest)
    logger.debug("Generated filter XML is: %s" % etree.tostring(parser_ingest))

    return parser_ingest
