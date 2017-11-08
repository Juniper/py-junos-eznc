from transitions import Machine
import pyparsing as pp
from collections import OrderedDict
import re
import copy


class Identifiers:
    printables = pp.OneOrMore(pp.Word(pp.printables))
    # numbers = pp.Word(pp.nums)
    numbers = (pp.Word(pp.nums)+pp.Optional(pp.Literal('.') + pp.Word(
        pp.nums))).setParseAction(lambda i: ''.join(i))
    hex_numbers = pp.OneOrMore(pp.Word(pp.nums, min=1)) & pp.OneOrMore(
        pp.Word('abcdefABCDEF', min=1))
    word = pp.Word(pp.alphanums) | pp.Word(pp.alphas)
    words = (pp.OneOrMore(word)).setParseAction(lambda i: ' '.join(i))
    percentage = pp.Word(pp.nums) + pp.Literal('%')
    header_bar = (pp.OneOrMore(pp.Word('-')) | pp.OneOrMore(pp.Word('='))) + \
                                              pp.StringEnd()


def data_type(item):
    # should use identifiers class attribute
    try:
        obj = Identifiers.numbers.parseString(item, parseAll=True)
        if '.' in obj[0]:
            return float
        else:
            return int
    except pp.ParseException as ex:
        pass
    try:
        Identifiers.hex_numbers.parseString(item, parseAll=True)
        return str   # special case
    except pp.ParseException as ex:
        pass
    return str


def convert_to_data_type(items):
    item_types = map(data_type, items)
    return map(lambda x, y: int(x) if y is int else x.strip(),
                     items, item_types)
    # return key, value


class StateMachine(Machine):

    def __init__(self, table_view):
        self._data = {}
        self._table = table_view
        self._view = self._table.VIEW
        self._raw = ''
        self._lines = []
        self.states = ['row_column', 'title_data', 'regex_data',
                       'delimiter_data', 'exists_bool_data']
        self.transitions = [
            {'trigger': 'column_provided', 'source': '*', 'dest': 'row_column',
             'conditions': 'match_columns', 'before': 'check_header_bar',
             'after': 'parse_raw_columns'},
            {'trigger': 'check_next_row', 'source': 'row_column', 'dest': 'row_column',
             'conditions': 'prev_next_row_same_type',
             'after': 'parse_raw_columns'},
            {'trigger': 'title_provided', 'source': 'start', 'dest': 'title_data',
             'conditions': ['match_title', 'title_not_followed_by_columns'],
             'after': 'parse_title_data'},
            {'trigger': 'regex_provided', 'source': 'title_data', 'dest': 'regex_data',
             'conditions': ['match_title'], 'before': 'check_header_bar',
             'after': 'parse_using_regex'},
            {'trigger': 'delimiter_without_title', 'source': 'start', 'dest': 'delimiter_data',
             'after': 'parse_using_delimiter'},
            {'trigger': 'delimiter_with_title', 'source': 'start', 'dest': 'delimiter_data',
             'conditions': ['match_title'], 'before': 'check_header_bar',
             'after': 'parse_using_delimiter'},
            {'trigger': 'regex_with_item', 'source': 'start',
             'dest': 'regex_data', 'after': 'parse_using_item_and_regex'},
            {'trigger': 'regex_parser', 'source': 'start',
             'dest': 'regex_data', 'after': 'parse_using_regex'},
            {'trigger': 'regex_parser', 'source': 'regex_data',
             'dest': 'regex_data', 'after': 'parse_using_regex'},
            {'trigger': 'regex_parser', 'source': 'row_column',
             'dest': 'regex_data', 'after': 'parse_using_regex'},
            {'trigger': 'exists_check', 'source': 'start',
             'dest': 'exists_bool_data', 'after': 'parse_exists'},
        ]
        Machine.__init__(self, states=self.states, transitions=self.transitions,
                         initial='start', send_event=True)

    def parse(self, lines):
        self._raw = '\n'.join(lines)
        self._lines = copy.deepcopy(lines)
        if self._table.DELIMITER is not None and self._view is None:
            if self._table.TITLE is not None:
                self.delimiter_with_title()
            else:
                self.delimiter_without_title()
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
                for key, value in self._view.FIELDS.items():
                    tbl = value['table']
                    tbl._view = tbl.VIEW
                    if tbl._view is None:
                        self._data[key] = StateMachine(tbl).parse(lines)
                        continue
                    if len(tbl._view.COLUMNS) > 0:
                        self._data[key] = StateMachine(tbl).parse(lines)
                    if tbl._view.TITLE is not None or tbl.TITLE is not None:
                        self._data[key] = StateMachine(tbl).parse(lines)
        return self._data

    def match_columns(self, event):
        columns = self._view.COLUMNS.values()
        if len(columns) == 0:
            return False
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
        line = self._lines[1]
        try:
            Identifiers.header_bar.parseString(line, parseAll=True)
            self._lines.pop(1)
        except pp.ParseException as ex:
            return False
        return True

    def parse_raw_columns(self, event):
        col_offsets = {}
        col_order = event.kwargs.get('col_order', OrderedDict())
        line = self._lines[0]
        if len(col_order) == 0:
            for key, column in self._view.COLUMNS.items():
                for result, start, end in pp.Literal(column).scanString(line):
                    col_offsets[(start, end)] = result[0]
            user_defined_columns = copy.deepcopy(self._view.COLUMNS)
            for key in sorted(col_offsets.iterkeys()):
                for x, y in self._view.COLUMNS.items():
                    if col_offsets[key] == user_defined_columns.get(x):
                        col_order[key] = x
                        user_defined_columns.pop(x)
                        break
        key = self._get_key(event.kwargs.get('key', self._table.KEY))
        items = re.split('\s\s+', self._lines[1].strip())

        post_integer_data_types = event.kwargs.get('check', map(data_type, items))
        index = event.kwargs.get('index', 1)
        # col_len = len(col_order)
        columns_list = col_order.values()
        for index, line in enumerate(self._lines[index:], start=index):
            items = re.split('\s\s+', line.strip())
            if len(items) >= len(columns_list):
                if len(items) > len(columns_list):
                    if col_offsets.keys()[0][0] > 10 and self._table.KEY == 'name':
                        columns_list.insert(0, self._table.KEY)
                    else:
                        items = items[:len(columns_list)]
                post_integer_data_types, pre_integer_data_types = \
                    map(data_type, items), post_integer_data_types
                if post_integer_data_types == pre_integer_data_types:
                    items = map(lambda data, typ: typ(data),
                                items, post_integer_data_types)
                    # try:
                    #     items = map(lambda data, typ: typ(data),
                    #                 items, post_integer_data_types)
                    # special case for hex values
                    # except ValueError as ex:
                    #     if "invalid literal for int() with base 10" in \
                    #             ex.message:
                    #         def fn(data, typ):
                    #             try:
                    #                 return typ(data)
                    #             except ValueError:
                    #                 return data
                    #         items = map(fn, items, post_integer_data_types)
                    tmp_dict = dict(zip(columns_list, items))
                    if isinstance(key, tuple):
                        if self._view.FILTERS is not None:
                            selected_dict = {}
                            for select in self._view.FILTERS:
                                if select in columns_list:
                                    selected_dict[select] = items[
                                        columns_list.index(
                                            select)]
                            if self._table.KEY_ITEMS is None:
                                self._data[tuple(tmp_dict[i] for i in key)] =\
                                 selected_dict
                            elif tmp_dict[key] in self._table.KEY_ITEMS:
                                self._data[tuple(tmp_dict[i] for i in key)] =\
                                 selected_dict
                        else:
                            self._data[tuple(tmp_dict[i] for i in key)] = \
                                tmp_dict
                    else:
                        if self._view.FILTERS is not None:
                            selected_dict = {}
                            for select in self._view.FILTERS:
                                if select in columns_list:
                                    selected_dict[select] = items[
                                        columns_list.index(
                                        select)]
                            if self._table.KEY_ITEMS is None:
                                self._data[tmp_dict[key]] = selected_dict
                            elif tmp_dict[key] in self._table.KEY_ITEMS:
                                self._data[tmp_dict[key]] = selected_dict
                        else:
                            if self._table.KEY_ITEMS is None:
                                self._data[tmp_dict[key]] = tmp_dict
                            elif tmp_dict[key] in self._table.KEY_ITEMS:
                                self._data[tmp_dict[key]] = tmp_dict
                else:
                    break
            elif line.strip() == '':
                self.check_next_row(check=post_integer_data_types, data=self._data,
                                    index=index, col_order=col_order,
                                    key=key)
        return self._data

    def _get_key(self, key):
        if isinstance(key, list):
            if set([i in self._view.COLUMNS or i in
                    self._view.COLUMNS.values() for i in key]):
                key_temp = []
                for i in key:
                    if i not in self._view.COLUMNS and i in \
                            self._view.COLUMNS.values():
                        for user_provided, from_table in self._view.COLUMNS.items():
                            # as dict will be created with user_provided key
                            if i == from_table or i == user_provided:
                                key_temp.append(user_provided)
                                break
                    else:
                        key_temp.append(i)
                key = tuple(key_temp)
        elif key not in self._view.COLUMNS and key in \
                self._view.COLUMNS.values():
            for user_provided, from_table in self._view.COLUMNS.items():
                if key == from_table:
                    key = user_provided
        key = key[0] if len(key) == 1 and isinstance(key, tuple) else key
        return key

    def prev_next_row_same_type(self, event):
        index = event.kwargs.get('index')
        post_integer_data_types = event.kwargs.get('check')
        line = self._lines[index]
        items = re.split('\s\s+', line.strip())
        post_integer_data_types, pre_integer_data_types = \
            map(data_type, items), post_integer_data_types
        return post_integer_data_types == pre_integer_data_types

    def parse_title_data(self, event):
        if self._view.REGEX != {}:
            return self.regex_provided()
        pre_space_delimit = ''
        delimiter = self._table.DELIMITER or '\s\s+'
        obj = re.search('(\s+).*', self._lines[1])
        if obj:
            pre_space_delimit = obj.group(1)
        for line in self._lines[1:]:
            if re.match(pre_space_delimit + '\s+', line):
                break
            if line.startswith(pre_space_delimit):
                try:
                    items = (re.split(delimiter, line.strip()))
                    item_types = map(data_type, items)
                    key, value = convert_to_data_type(items)
                    if self._table.KEY_ITEMS is None:
                        self._data[self._view.FIELDS.get(key, key)] = value
                    elif key in self._table.KEY_ITEMS:
                        self._data[self._view.FIELDS.get(key, key)] = value
                except ValueError:
                    regex = '(\d+)\s(.*)' if item_types[0] == int else '(' \
                                                                      '.*)\s(\d+)'
                    obj = re.search(regex, line)
                    if obj:
                        items = obj.groups()
                        key, value = convert_to_data_type(items)
                        self._data[key] = value
            elif line.strip() == '':
                break
        return self._data

    def parse_using_regex(self, event):
        _regex = copy.deepcopy(self._view.REGEX)
        for key, val in _regex.items():
            if val in Identifiers.__dict__:
                _regex[key] = Identifiers.__dict__[val]
            else:
                _regex[key] = pp.Regex(val, flags=re.IGNORECASE)

        _regex = reduce(lambda x, y: x+y, _regex.values())
        for index, line in enumerate(self._lines[1:]):
            tmp_dict = {}
            # checking index as there can be blank line at position 0 and 2
            if line.strip() == '':
                if self.is_row_column() and index > 2:
                    try:
                        if len(_regex.scanString(self._lines[self._lines.index(
                                line)+1])[0]) == 0:
                            break
                    except IndexError:
                        break
                else:
                    continue
            for result, start, end in _regex.scanString(line):
                # write a different function for this
                for key, val in self._view.REGEX.items():
                    if val not in Identifiers.__dict__:
                        obj = re.search(val, result[self._view.REGEX.keys(

                        ).index(
                            key)], re.I)
                        if obj and len(obj.groups()) >= 1:
                            result[self._view.REGEX.keys().index(key)] = \
                                obj.groups()[0]
                tmp_dict = dict(zip(self._view.REGEX.keys(),
                                    convert_to_data_type(result)))
            if len(tmp_dict) > 0:
                if tmp_dict.get(self._table.KEY) is None:
                    self._data.update(tmp_dict)
                else:
                    self._data[tmp_dict.get(self._table.KEY)] = tmp_dict

    def parse_using_item_and_regex(self, event):
        if self._table.ITEM=='*':
            for key, regex in self._view.REGEX.items():
                obj = re.search(regex, self._raw)
                if obj:
                    val = obj.groups()[0] if len(obj.groups()) >= 1 else \
                        obj.group()
                    self._data[key] = data_type(val)(val)
        else:
            key = self._get_key(event.kwargs.get('key', self._table.KEY))
            for line in re.finditer("%s .*" % self._table.ITEM, '\n'.join(
                    self._lines)):
                tmp_dict = {}
                for k, exp in self._view.REGEX.items():
                    obj = re.search(exp, line.group())
                    if obj:
                        val = obj.groups()[0] if len(obj.groups()) >= 1 else \
                            obj.group()
                        tmp_dict[k] = data_type(val)(val)
                if key in tmp_dict:
                    self._data[tmp_dict[key]] = tmp_dict

    def parse_using_delimiter(self, event):
        delimiter = self._table.DELIMITER
        pre_space_delimit = ''
        if self._table.TITLE is None:
            for line in self._lines[1:]:
                if line.strip() == 'SENT: Ukern command: %s'%self._table.GET_CMD:
                    self._lines = self._lines[self._lines.index(line)+1:]
                    break
        else:
            obj = re.search('^(\s+).*', self._lines[1])
            if obj:
                pre_space_delimit = obj.group(1)
        for index, line in enumerate(self._lines[1:]):
            if line.strip() == '':
                if index > 2:
                    break
                else:
                    continue
            if line.startswith(pre_space_delimit):
                try:
                    items = (re.split(delimiter, line.strip()))
                    key, value = convert_to_data_type(items)
                    self._data[key] = value
                except ValueError as ex:
                    # create a class named ParseError
                    raise Exception('Not able to parse line: %s'%line)
            else:
                break
        return self._data

    def parse_exists(self, event):
        for key, search in self._view.EXISTS.items():
            self._data[key] = re.search(search, self._raw, re.I|re.M) is not \
                              None
