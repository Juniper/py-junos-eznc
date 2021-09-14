from collections import OrderedDict
from functools import reduce
import re
import copy
import logging

from jinja2 import Template, meta
from transitions import Machine
import pyparsing as pp

logger = logging.getLogger("jnpr.junos.factory.state_machine")


class Identifiers:
    """
    This class static variables can be used when defining regex view. For ex:
    _PFENotificationStatsTable:
      title: PFE Notification statistics
      key: name
      view: _PFENotificationStatsView

    _PFENotificationStatsView:
      regex:
        value: numbers
        name: words
    """

    printables = pp.OneOrMore(pp.Word(pp.printables))
    numbers = (
        pp.Word(pp.nums) + pp.Optional(pp.Literal(".") + pp.Word(pp.nums))
    ).setParseAction(lambda i: "".join(i))
    hex_numbers = pp.OneOrMore(pp.Word(pp.nums, min=1)) & pp.OneOrMore(
        pp.Word("abcdefABCDEF", min=1)
    )
    word = pp.Word(pp.alphanums) | pp.Word(pp.alphas)
    words = (pp.OneOrMore(word)).setParseAction(lambda i: " ".join(i))
    percentage = pp.Word(pp.nums) + pp.Literal("%")
    header_bar = (
        pp.OneOrMore(pp.Word("-")) | pp.OneOrMore(pp.Word("="))
    ) + pp.StringEnd()


def data_type(item):
    """

    Args:
        item: string element parsed from the blob.

    Returns: item converted to data type it should represent

    """
    try:
        obj = Identifiers.numbers.parseString(item, parseAll=True)
        if "." in obj[0]:
            return float
        else:
            return int
    except pp.ParseException as ex:
        pass
    try:
        Identifiers.hex_numbers.parseString(item, parseAll=True)
        return str  # special case
    except pp.ParseException as ex:
        pass
    return str


def convert_to_data_type(items):
    """

    Args:
        items: list of string objects

    Returns: list of converted data type objects

    """
    item_types = map(data_type, items)
    return list(map(lambda x, y: int(x) if y is int else x.strip(), items, item_types))


class StateMachine(Machine):
    def __init__(self, table_view):
        self._data = {}
        self._table = table_view
        self._view = self._table.VIEW
        self._raw = ""
        self._lines = []
        self.states = [
            "row_column",
            "title_data",
            "regex_data",
            "delimiter_data",
            "exists_bool_data",
        ]
        self.transitions = [
            {
                "trigger": "column_provided",
                "source": "*",
                "dest": "row_column",
                "conditions": "match_columns",
                "before": "check_header_bar",
                "after": "parse_raw_columns",
            },
            {
                "trigger": "check_next_row",
                "source": "row_column",
                "dest": "row_column",
                "conditions": "prev_next_row_same_type",
                "after": "parse_raw_columns",
            },
            {
                "trigger": "title_provided",
                "source": "start",
                "dest": "title_data",
                "conditions": ["match_title", "title_not_followed_by_columns"],
                "after": "parse_title_data",
            },
            {
                "trigger": "regex_provided",
                "source": "title_data",
                "dest": "regex_data",
                "conditions": ["match_title"],
                "before": "check_header_bar",
                "after": "parse_using_regex",
            },
            {
                "trigger": "delimiter_without_title",
                "source": "start",
                "dest": "delimiter_data",
                "after": "parse_using_delimiter",
            },
            {
                "trigger": "delimiter_with_title",
                "source": ["start", "delimiter_data"],
                "dest": "delimiter_data",
                "conditions": ["match_title"],
                "before": "check_header_bar",
                "after": "parse_using_delimiter",
            },
            {
                "trigger": "regex_with_item",
                "source": ["start", "regex_data"],
                "dest": "regex_data",
                "after": "parse_using_item_and_regex",
            },
            {
                "trigger": "regex_parser",
                "source": "start",
                "dest": "regex_data",
                "after": "parse_using_regex",
            },
            {
                "trigger": "regex_parser",
                "source": "regex_data",
                "dest": "regex_data",
                "after": "parse_using_regex",
            },
            {
                "trigger": "regex_parser",
                "source": "row_column",
                "dest": "regex_data",
                "after": "parse_using_regex",
            },
            {
                "trigger": "exists_check",
                "source": ["start", "regex_data", "row_column"],
                "dest": "exists_bool_data",
                "after": "parse_exists",
            },
            {
                "trigger": "exists_check",
                "source": "title_data",
                "dest": "exists_bool_data",
                "after": "parse_exists",
            },
        ]
        Machine.__init__(
            self,
            states=self.states,
            transitions=self.transitions,
            initial="start",
            send_event=True,
        )

    def parse(self, lines):
        """
        Starting point to parse string blob section. In case of nested table
        this API will get called in recursive call.

        Args:
            lines: list of lines which was received from rpc reply <output>.

        Returns: dictionary (self._data) with parsed data.

        """
        self._lines = copy.deepcopy(lines)
        self._raw = "\n".join(lines)
        if self._view is None:
            if self._table.DELIMITER is not None:
                if self._table.TITLE is not None:
                    self.delimiter_with_title()
                else:
                    self.delimiter_without_title()
            elif self._table.TITLE is not None:
                self.title_provided()
            elif self._table.ITEM is not None and self._table.ITEM != "*":
                self._parse_item_iter(lines)
        else:
            if self._view.TITLE is not None or self._table.TITLE:
                self.title_provided()
            if len(self._view.REGEX) > 0:
                if self._table.ITEM is not None:
                    self.regex_with_item()
                else:
                    self.regex_parser()
            if len(self._view.COLUMNS) > 0:
                self.column_provided()
            if len(self._view.EXISTS) > 0:
                self.exists_check()
            if len(self._view.FIELDS) > 0:
                if self._table.ITEM is not None and self._table.ITEM != "*":
                    return self._parse_item_iter(lines)
                for key, value in self._view.FIELDS.items():
                    tbl = value["table"]
                    tbl._view = tbl.VIEW
                    if tbl._view is None:
                        self._data[key] = StateMachine(tbl).parse(lines)
                        continue
                    if len(tbl._view.COLUMNS) > 0:
                        self._data[key] = StateMachine(tbl).parse(lines)
                    if tbl._view.TITLE is not None or tbl.TITLE is not None:
                        self._data[key] = StateMachine(tbl).parse(lines)
        if self._table.EVAL:
            self._eval_in_full_data()
        return self._data

    def _eval_in_full_data(self):
        """
        To eval expression from full set of data (self._data). Sets key in
        self._data itself.

        Returns: None
        """
        for name, expression in self._table.EVAL.items():
            t = Template(expression)
            expression = t.render(data=self._data)
            try:
                val = eval(expression)
            except Exception as ex:
                logger.error("eval expression for '%s' failed due to %s" % (name, ex))
                self._data[name] = None
            else:
                self._data[name] = val

    def _parse_item_iter(self, lines):
        """
        There are cases when similar data set repeats. With item its easier to
        split string blob into different sections.
        Args:
            lines: list of lines

        Returns: dictionary (self._data) with parsed data.

        """
        self._raw = "\n".join(lines)
        pat = pp.Regex(self._table.ITEM)
        x = []
        for result, start, end in pat.scanString(self._raw):
            x.append((start, end))
        for i in range(len(x)):
            try:
                raw = self._raw[x[i][0] : x[i + 1][0]]
            except IndexError:
                raw = self._raw[x[i][0] :]
            lines = raw.splitlines()
            obj = re.search(self._table.ITEM, lines[0])
            groups = obj.groups()
            groups = [data_type(val)(val) for val in groups]
            if len(groups) >= 1:
                if len(groups) != len(
                    self._table.KEY
                    if isinstance(self._table.KEY, list)
                    else [self._table.KEY]
                ):
                    raise KeyError(
                        "Table with grouped item must contain " "corresponding key(s)"
                    )
                master_key = groups[0] if len(groups) == 1 else tuple(groups)
                self._data[master_key] = {}
                if self._view is not None:
                    for key, value in self._view.FIELDS.items():
                        tbl = value["table"]
                        tbl._view = tbl.VIEW
                        if tbl._view is not None and len(tbl._view.COLUMNS) > 0:
                            self._data[master_key][key] = StateMachine(tbl).parse(lines)
                        if tbl.TITLE is not None or tbl._view.TITLE is not None:
                            self._data[master_key][key] = StateMachine(tbl).parse(lines)
                else:
                    self._table.TITLE = lines[0]
                    delimiter = self._table.DELIMITER or "\s\s+"
                    temp_dict = {}
                    pre_space_delimit = self._get_pre_space_delimiter(lines[1])
                    for line in lines[1:]:
                        if re.match(pre_space_delimit + "\s+", line):
                            break
                        if line.startswith(pre_space_delimit):
                            try:
                                items = re.split(delimiter, line.strip())
                                item_types = list(map(data_type, items))
                                key, value = convert_to_data_type(items)
                                temp_dict[key] = value
                            except ValueError:
                                regex = (
                                    "(\d+)\s(.*)"
                                    if item_types[0] == int
                                    else "(" ".*)\s(\d+)"
                                )
                                obj = re.search(regex, line)
                                if obj:
                                    items = obj.groups()
                                    key, value = convert_to_data_type(items)
                                    temp_dict[key] = value
                        # check if next line is blank or new title (delimiter
                        # test to fail)
                        elif (
                            line.strip() == ""
                            or len(re.split(delimiter, line.strip())) <= 1
                        ):
                            break
                    self._insert_eval_data(temp_dict)
                    self._data[master_key] = temp_dict
        return self._data

    def match_columns(self, event):
        if self._view is None:
            return False
        columns = self._view.COLUMNS.values()
        if len(columns) == 0:
            return False
        if True in [isinstance(i, list) for i in columns]:
            # we have multi line column header
            columns = [[i] if isinstance(i, str) else i for i in columns]
            max_title_len = reduce(
                lambda x, y: x if x > y else y, map(lambda x: len(x), columns)
            )
            for index, item in enumerate(columns):
                columns[index] = item + [None] * (max_title_len - len(item))
            col_parser = reduce(lambda x, y: x & y, [pp.Literal(i[0]) for i in columns])
            for line in self._lines:
                if self._parse_literal(line, col_parser):
                    for index in range(1, max_title_len):
                        col_parser = reduce(
                            lambda x, y: x & y,
                            [
                                pp.Literal(i[index])
                                for i in columns
                                if i[index] is not None
                            ],
                        )
                        if self._parse_literal(
                            self._lines[self._lines.index(line) + 1], col_parser
                        ):
                            # removing next lines in header title, dont see any
                            # use of these lines
                            self._lines.pop(self._lines.index(line) + 1)
                        else:
                            return False
                    current_index = self._lines.index(line)
                    self._lines = self._lines[current_index:]
                    return True
                else:
                    continue
        else:
            col_parser = reduce(lambda x, y: x & y, [pp.Literal(i) for i in columns])
            for line in self._lines:
                if self._parse_literal(line, col_parser):
                    d = set(map(lambda x, y: x in y, columns, [line] * len(columns)))
                    if d.pop():
                        current_index = self._lines.index(line)
                        self._lines = self._lines[current_index:]
                        return True
            return False

    def match_title(self, event):
        """
        To check whether given title exists in string blob.

        Args:
            event: In case any data is supposed to be passed.

        Returns: Boolean value depending on matching of title

        """
        title = self._table.TITLE or self._view.TITLE
        for line in self._lines:
            if title in line:
                current_index = self._lines.index(line)
                self._lines = self._lines[current_index:]
                return True
        return False

    def title_not_followed_by_columns(self, event):
        return not self.match_columns(event)

    def _parse_literal(self, line, col_parser):
        try:
            if col_parser.searchString(line):
                return True
        except pp.ParseException as ex:
            return False

    def check_header_bar(self, event):
        """
        Remove redundant title bar line from lines.
        Args:
            event:

        Returns: Boolean depending on if the next line is a title bar or not.

        For example, here if we provide columns, we need to get rid of next line
        ---------------------------------------
        Module  Name              Active Errors
        ---------------------------------------
        1       PQ3 Chip          0
        2       Host Loopback     0

        """
        line = self._lines[1]
        try:
            Identifiers.header_bar.parseString(line, parseAll=True)
            self._lines.pop(1)
        except pp.ParseException as ex:
            return False
        return True

    def parse_raw_columns(self, event):
        col_offsets = {}
        col_order = event.kwargs.get("col_order", OrderedDict())
        line = self._lines[0]
        column = self._view.COLUMNS
        if True in [isinstance(i, list) for i in column.values()]:
            # just take first line of column title
            for k, v in column.items():
                if isinstance(v, list):
                    column[k] = v[0]
        if len(col_order) == 0:
            for key, val in column.items():
                for result, start, end in pp.Literal(val).scanString(line):
                    col_offsets[(start, end)] = result[0]
            user_defined_columns = copy.deepcopy(self._view.COLUMNS)
            for key in sorted(col_offsets.keys()):
                for x, y in self._view.COLUMNS.items():
                    if col_offsets[key] == user_defined_columns.get(x):
                        col_order[key] = x
                        user_defined_columns.pop(x)
                        break
        key = self._get_key(event.kwargs.get("key", self._table.KEY))
        items = re.split("\s\s+", self._lines[1].strip())

        post_integer_data_types = event.kwargs.get("check", list(map(data_type, items)))
        index = event.kwargs.get("index", 1)
        # col_len = len(col_order)
        columns_list = list(col_order.values())
        for index, line in enumerate(self._lines[index:], start=index):
            items = re.split("\s\s+", line.strip())
            if len(items) >= len(columns_list):
                if len(items) > len(columns_list):
                    if (
                        list(col_offsets.keys())[0][0] > 10
                        and self._table.KEY == "name"
                    ):
                        columns_list.insert(0, self._table.KEY)
                    else:
                        items = items[: len(columns_list)]
                post_integer_data_types, pre_integer_data_types = (
                    list(map(data_type, items)),
                    post_integer_data_types,
                )
                if post_integer_data_types == pre_integer_data_types:
                    items = list(
                        map(lambda data, typ: typ(data), items, post_integer_data_types)
                    )
                    tmp_dict = dict(zip(columns_list, items))
                    self._insert_data(key, tmp_dict, columns_list)
                else:
                    break
            elif line.strip() == "":
                # first check if loop already reached at the end of command o/p
                if not index + 1 >= len(self._lines):
                    self.check_next_row(
                        check=post_integer_data_types,
                        data=self._data,
                        index=index,
                        col_order=col_order,
                        key=key,
                    )
        return self._data

    def _insert_data(self, key, tmp_dict, columns_list):
        """
        Insert data per row into main dictionary self._data

        Args:
            key: To be used as key to dictionary
            tmp_dict: Temporary dictionary to be populated
            columns_list: Columns defined by the users

        Returns: None, function just populates self._data

        """
        self._insert_eval_data(tmp_dict)
        if isinstance(key, (tuple, list)):
            if self._view.FILTERS is not None:
                selected_dict = {}
                for select in self._view.FILTERS:
                    if select in columns_list:
                        selected_dict[select] = tmp_dict[select]
                if self._table.KEY_ITEMS is None:
                    self._data[tuple(tmp_dict[i] for i in key)] = selected_dict
                elif tmp_dict[key] in self._table.KEY_ITEMS:
                    self._data[tuple(tmp_dict[i] for i in key)] = selected_dict
            else:
                self._data[tuple(tmp_dict[i] for i in key)] = tmp_dict
        else:
            if self._view.FILTERS is not None:
                selected_dict = {}
                for select in self._view.FILTERS:
                    if select in columns_list:
                        selected_dict[select] = tmp_dict[select]
                if self._table.KEY_ITEMS is None:
                    self._data[tmp_dict[key]] = selected_dict
                elif tmp_dict[key] in self._table.KEY_ITEMS:
                    self._data[tmp_dict[key]] = selected_dict
            else:
                if self._table.KEY_ITEMS is None:
                    if key not in tmp_dict:
                        self._data.update(tmp_dict)
                    else:
                        self._data[tmp_dict[key]] = tmp_dict
                elif tmp_dict[key] in self._table.KEY_ITEMS:
                    self._data[tmp_dict[key]] = tmp_dict

    def _get_key(self, key):
        """
        Fetch the key from columns which will be used to define dictionary
        Args:
            key: user defined key input

        Returns: key to be used in dictionary.

        """
        if isinstance(key, list):
            if set(
                [
                    i in self._view.COLUMNS or i in self._view.COLUMNS.values()
                    for i in key
                ]
            ):
                key_temp = []
                for i in key:
                    if i not in self._view.COLUMNS and i in self._view.COLUMNS.values():
                        for user_provided, from_table in self._view.COLUMNS.items():
                            # as dict will be created with user_provided key
                            if i == from_table or i == user_provided:
                                key_temp.append(user_provided)
                                break
                    else:
                        key_temp.append(i)
                key = tuple(key_temp)
        elif key not in self._view.COLUMNS and key in self._view.COLUMNS.values():
            for user_provided, from_table in self._view.COLUMNS.items():
                if key == from_table:
                    key = user_provided
        key = key[0] if len(key) == 1 and isinstance(key, tuple) else key
        return key

    def prev_next_row_same_type(self, event):
        """
        Checks if the consecutive two lines of similar types.

        Args:
            event: takes parameter from the API call

        Returns: Boolean, depending if two lines are of similar types.

        """
        index = event.kwargs.get("index")
        post_integer_data_types = event.kwargs.get("check")
        line = self._lines[index]
        items = re.split("\s\s+", line.strip())
        post_integer_data_types, pre_integer_data_types = (
            list(map(data_type, items)),
            post_integer_data_types,
        )
        return post_integer_data_types == pre_integer_data_types

    def _get_pre_space_delimiter(self, line):
        """
        Sometime all the data lines under a table is withing some space limit
        which gives a easy way to stop looking for lines if the delimiter is not
        followed.
        Args:
            line: should be first line after title

        Returns: decide how much space to be considered as delimiter

        For example, in below output, all data for FPCx has 2 space delimiter

        Statistics for port 1 connected to device FPC1:
          TX Packets 64 Octets        96106518
          TX Packets 65-127 Octets    56224217
          TX Packets 128-255 Octets   4550198
          TX Packets 256-511 Octets   1841
          TX Packets 512-1023 Octets  1354
        Statistics for port 1 connected to device FPC2:
          TX Packets 64 Octets        345354435
          TX Packets 65-127 Octets    34531
          TX Packets 128-255 Octets   4351451
          TX Packets 256-511 Octets   1345
          TX Packets 512-1023 Octets  526513
        """
        pre_space_delimit = ""
        obj = re.search("(\s+).*", line)
        if obj:
            pre_space_delimit = obj.group(1)
        return pre_space_delimit

    def parse_title_data(self, event):
        """
        title description in Table helps to get the starting point for starting
        search

        Args:
            event: In case trigger want to pass some data

        Returns: None, Just add corresponding key, value to existing dict

        Let say we have CLI "show xmchip 0 pt stats" output as:

        WAN PT statistics (Index 0)
        ---------------------------

        PCT entries used by all WI-1 streams         : 0
        PCT entries used by all WI-0 streams         : 0
        PCT entries used by all LI streams           : 0
        CPT entries used by all multicast packets    : 0
        CPT entries used by all WI-1 streams         : 0
        CPT entries used by all WI-0 streams         : 0
        CPT entries used by all LI streams           : 0

        Fabric PT statistics (Index 1)
        ------------------------------

        PCT entries used by all FI streams           : 0
        PCT entries used by all WI (Unused) streams  : 0
        PCT entries used by all LI streams           : 0
        CPT entries used by all multicast packets    : 0
        CPT entries used by all FI streams           : 0
        CPT entries used by all WI (Unused) streams  : 0
        CPT entries used by all LI streams           : 0

        With below table/view to parse the data
        ---
        XMChipStatsTable:
          command: show xmchip 0 pt stats
          target: fpc1
          view: XMChipStatsView

        XMChipStatsView:
          fields:
            wan_pt_stats: _WANPTStatTable
            fabric_pt_stats: _FabricPTStatTable

        _WANPTStatTable:
          title: WAN PT statistics (Index 0)
          delimiter: ":"

        _FabricPTStatTable:
          title: Fabric PT statistics (Index 1)
          delimiter: ":"

        which returns:
        {'fabric_pt_stats': {'CPT entries used by all FI streams': 0,
                     'CPT entries used by all LI streams': 0,
                     'CPT entries used by all WI (Unused) streams': 0,
                     'CPT entries used by all multicast packets': 0,
                     'PCT entries used by all FI streams': 0,
                     'PCT entries used by all LI streams': 0,
                     'PCT entries used by all WI (Unused) streams': 0},
        'wan_pt_stats': {'CPT entries used by all LI streams': 0,
                     'CPT entries used by all WI-0 streams': 0,
                     'CPT entries used by all WI-1 streams': 0,
                     'CPT entries used by all multicast packets': 0,
                     'PCT entries used by all LI streams': 0,
                     'PCT entries used by all WI-0 streams': 0,
                     'PCT entries used by all WI-1 streams': 0}}
        """
        if self._view is not None and self._view.REGEX != {}:
            return self.regex_provided()
        # view have only fields, so contains only nested table
        if (
            self._view is not None
            and self._view.FIELDS
            and not self._view.COLUMNS
            and not self._view.REGEX
        ):
            return
        delimiter = self._table.DELIMITER or "\s\s+"
        pre_space_delimit = self._get_pre_space_delimiter(self._lines[1])
        for line in self._lines[1:]:
            if re.match(pre_space_delimit + "\s+", line):
                break
            if line.startswith(pre_space_delimit):
                try:
                    items = re.split(delimiter, line.strip())
                    item_types = list(map(data_type, items))
                    key, value = convert_to_data_type(items)
                    if self._view is None:
                        self._data[key] = value
                    elif self._table.KEY_ITEMS is None:
                        self._data[self._view.FIELDS.get(key, key)] = value
                    elif key in self._table.KEY_ITEMS:
                        self._data[self._view.FIELDS.get(key, key)] = value
                except ValueError:
                    regex = "(\d+)\s(.*)" if item_types[0] == int else "(" ".*)\s(\d+)"
                    obj = re.search(regex, line)
                    if obj:
                        items = obj.groups()
                        key, value = convert_to_data_type(items)
                        self._data[key] = value
            # check if next line is blank or new title (delimiter test to fail)
            elif line.strip() == "" or len(re.split(delimiter, line.strip())) <= 1:
                break
        return self._data

    def parse_using_regex(self, event):
        """
        All the regex should add up to match a line

        Args:
            event: In case trigger want to pass some data

        Returns: None, Just add corresponding key, value to existing dict

        Let say we have CLI "show system processes extensive" output as:

        PID USERNAME  HR PRI NICE   SIZE    RES STATE   C   TIME    WCPU COMMAND
           11 root       2 155 ki31     0K    32K RUN     0 3214.6 191.31% idle
        19542 root       2  22    0   808M 49872K select  1  90.9H   3.86% chas
        19679 root       1  33    0   723M 1208K select  0 839:37   0.49% python
        19451 root       1  20    0   720M 1052K select  1  60:37   0.20% eventd
           12 root       26 -60    -     0K   416K WAIT    1 635:29   0.00% intr

        With a regex table as below
        ---
        SystemProcExtTable:
          command: show system processes extensive
          key: cmd
          view: SystemProcExtView

        SystemProcExtView:
          regex:
            pid: '\d+'
            wcpu: '.*(\d+\.\d+)%'
            cmd: '\w+'

        which returns something like (data for representation only):
        {'alarm': {'cmd': 'alarm', 'pid': 20483, 'wcpu': '0.00'},
         'alarmd': {'cmd': 'alarmd', 'pid': 20473, 'wcpu': '0.00'},
         'appidd': {'cmd': 'appidd', 'pid': 19686, 'wcpu': '0.00'},
         'apsd': {'cmd': 'apsd', 'pid': 20435, 'wcpu': '0.00'},
        """
        _regex = copy.deepcopy(self._view.REGEX)
        for key, val in _regex.items():
            if val in Identifiers.__dict__:
                _regex[key] = Identifiers.__dict__[val]
            else:
                _regex[key] = pp.Regex(val, flags=re.IGNORECASE)

        _regex = reduce(lambda x, y: x + y, _regex.values())
        for index, line in enumerate(self._lines):
            tmp_dict = {}
            # checking index as there can be blank line at position 0 and 2
            if line.strip() == "":
                if index > 2:
                    if self.is_row_column() or self.is_regex_data():
                        try:
                            match = []
                            # check if line after new line matches condition
                            # There can be data set where there are new line in between.
                            for result, start, end in _regex.scanString(
                                self._lines[index + 1]
                            ):
                                match.extend(result)
                            if match:
                                continue
                            else:
                                break
                        except IndexError:
                            break
                else:
                    continue
            for result, start, end in _regex.scanString(line):
                # write a different function for this
                for key, val in self._view.REGEX.items():
                    if val not in Identifiers.__dict__:
                        obj = re.search(
                            val, result[list(self._view.REGEX.keys()).index(key)], re.I
                        )
                        if obj and len(obj.groups()) >= 1:
                            result[
                                list(self._view.REGEX.keys()).index(key)
                            ] = obj.groups()[0]
                items = convert_to_data_type(result)
                tmp_dict = dict(zip(self._view.REGEX.keys(), items))
                if len(tmp_dict) > 0:
                    self._insert_data(
                        self._table.KEY, tmp_dict, list(self._view.REGEX.keys())
                    )

    def parse_using_item_and_regex(self, event):
        """
        when multiple map is provided for regex, they gets added to search each
        line. But when item is '*' each regex item is used to search given value
        regular expression in whole string blob.

        Args:
            event: In case trigger want to pass some data

        Returns: None, Just add corresponding key, value to existing dict

        Let say we have CLI "show xmchip 0 pt stats" output as:

        PCT entries used by all WI-1 streams         : 21
        PCT entries used by all WI-0 streams         : 34
        PCT entries used by all LI streams           : 0
        CPT entries used by all multicast packets    : 0
        CPT entries used by all WI-1 streams         : 0
        CPT entries used by all WI-0 streams         : 0
        CPT entries used by all LI streams           : 0

        ---
        XMChipStatsTable:
          command: show xmchip {{ instance }} pt stats
          args:
            instance: 0
          target: fpc2
          item: '*'
          view: XMChipStatsView

        XMChipStatsView:
          regex:
            pct_wi_1: 'PCT entries used by all WI-1 streams\s+:\s?(\d+)'
            pct_wi_0: 'PCT entries used by all WI-0 streams\s+:\s?(\d+)'

        which returns:
        {'pct_wi_1': 0, 'pct_wi_0': 0}
        """
        if self._table.ITEM == "*":
            self._raw = "\n".join(self._lines)
            for key, regex in self._view.REGEX.items():
                obj = re.search(regex, self._raw)
                if obj:
                    val = obj.groups()[0] if len(obj.groups()) >= 1 else obj.group()
                    self._data[key] = data_type(val)(val)
            self._insert_eval_data(self._data)
        else:
            key = self._get_key(event.kwargs.get("key", self._table.KEY))
            for line in re.finditer("%s .*" % self._table.ITEM, "\n".join(self._lines)):
                tmp_dict = {}
                for k, exp in self._view.REGEX.items():
                    obj = re.search(exp, line.group())
                    if obj:
                        val = obj.groups()[0] if len(obj.groups()) >= 1 else obj.group()
                        tmp_dict[k] = data_type(val)(val)
                self._insert_eval_data(tmp_dict)
                if key in tmp_dict:
                    self._data[tmp_dict[key]] = tmp_dict
        return self._data

    def parse_using_delimiter(self, event):
        """

        Args:
            event: In case trigger want to pass some data

        Returns: None, Just add corresponding key, value to existing dict

        For a given cli "show link stats" output:
        PPP LCP/NCP: 0
        HDLC keepalives: 0
        RSVP: 0
        ISIS: 0
        OSPF Hello: 541025
        OAM:  0
        BFD:  15
        UBFD:  0
        LMI:  0
        LACP: 0
        ETHOAM: 0
        SYNCE:  0
        PTP:  0
        L2TP:  0
        LNS-PPP:  0
        ARP:  4307
        ELMI:  0
        VXLAN MRESOLVE: 0
        Unknown protocol: 42

        Lets say we can have table as
        ---
        FPCLinkStatTable:
            command: show link stats
            target: fpc1
            delimiter: ":"

        which given return value as
        {'ARP': 4307, 'ELMI': 0, 'SYNCE': 0, 'ISIS': 0, 'BFD': 15,
        'PPP LCP/NCP': 0, 'OAM': 0, 'ETHOAM': 0, 'LACP': 0, 'LMI': 0,
        'Unknown protocol': 42, 'UBFD': 0, 'L2TP': 0, 'HDLC keepalives': 0,
        'LNS-PPP': 0, 'OSPF Hello': 541025, 'RSVP': 0, 'VXLAN MRESOLVE': 0,
        'PTP': 0}

        """
        delimiter = self._table.DELIMITER or "\s\s+"
        pre_space_delimit = ""
        if self._table.TITLE is None:
            for line in self._lines[1:]:
                if line.strip() == "SENT: Ukern command: %s" % self._table.GET_CMD:
                    self._lines = self._lines[self._lines.index(line) + 1 :]
                    break
        else:
            obj = re.search("^(\s+).*", self._lines[1])
            if obj:
                pre_space_delimit = obj.group(1)
        for index, line in enumerate(self._lines[1:]):
            if line.strip() == "":
                if index > 2:
                    break
                else:
                    continue
            if line.startswith(pre_space_delimit):
                try:
                    items = re.split(delimiter, line.strip())
                    key, value = convert_to_data_type(items)
                    if self._table.KEY_ITEMS is None:
                        self._data[key] = value
                    elif key in self._table.KEY_ITEMS:
                        self._data[key] = value
                except ValueError as ex:
                    # create a class named ParseError
                    raise Exception("Not able to parse line: %s" % line)
            else:
                break
        return self._data

    def parse_exists(self, event):
        """

        Args:
            event: In case trigger want to pass some data

        Returns: None, Just add corresponding key, value to existing dict. Value
         here is a boolean

        ---
        HostlbStatusSummaryTable:
          command: show host_loopback status-summary
          target: Null
          view: HostlbStatusSummaryView

        HostlbStatusSummaryView:
          exists:
            no_detected_wedges: No detected wedges
            no_toolkit_errors: No toolkit errors

        should give something like
        {'no_detected_wedges': True, 'no_toolkit_errors': True}
        """
        for key, search in self._view.EXISTS.items():
            self._data[key] = re.search(search, self._raw, re.I | re.M) is not None

    def _insert_eval_data(self, tmp_dict):
        """

        Args:
            tmp_dict: dictionary of key value from a iteration of view

        Returns: if there is any eval expression in view, does the eval using
        tmp_dictionary. For example:

        ---
        XMChipStatsTable:
          command: show xmchip {{ instance }} pt stats
          args:
            instance: 0
          target: fpc2
          item: '*'
          view: XMChipStatsView

        XMChipStatsView:
          regex:
            pct_wi_1: 'PCT entries used by all WI-1 streams\s+:\s?(\d+)'
            pct_wi_0: 'PCT entries used by all WI-0 streams\s+:\s?(\d+)'
          eval:
            total_pct: '{{ pct_wi_1 }} + {{ pct_wi_0 }}'

        which returns
        {'pct_wi_1': 0, 'pct_wi_0': 0, 'total_pct': 0}
        """
        if self._view and len(self._view.EVAL) > 0:
            for name, expression in self._view.EVAL.items():
                variables = meta.find_undeclared_variables(expression)
                t = Template(expression)
                expression = t.render({k: tmp_dict.get(k) for k in variables})
                val = eval(expression)
                tmp_dict[name] = val
