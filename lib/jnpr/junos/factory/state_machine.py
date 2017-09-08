from transitions import Machine
import pyparsing as pp
from collections import OrderedDict
import re
import copy

class Identifiers:
    printables = pp.printables
    numbers = pp.Word(pp.nums)
    word = pp.Word(pp.alphanums) | pp.Word(pp.alphas)
    words = pp.OneOrMore(word)
    percentage = pp.Word(pp.nums) + pp.Literal('%')


def is_integer(item):
    try:
        Identifiers.numbers.parseString(item, parseAll=True)
    except pp.ParseException as ex:
        return False
    return True

class StateMachine(Machine):

    def __init__(self, table_view):
        self._table = table_view
        self._view = self._table.VIEW
        # self._identifiers = [Identifiers.__dict__[key] for key, val in
                             # Identifiers.__dict__.items() if callable(val)]
        # self._identifiers = [pp.OneOrMore(word)]
        self._lines = []
        self.states = ['row_column']
        self.transitions = [
            {'trigger': 'column_provided', 'source': 'start', 'dest': 'row_column',
             'conditions': 'match_columns', 'after': 'parse_raw_column'}, ]
        Machine.__init__(self, states=self.states, transitions=self.transitions,
                         initial='start', send_event=True)

    def parse(self, raw_data):
        self._data = {}
        self._lines = raw_data.splitlines()
        if self._view.COLUMN is not None:
            self.column_provided()
        return self._data

    def match_columns(self, event):
        columns = self._view.COLUMN.values()
        for line in self._lines:
            d = set(map(lambda x, y: x in y, columns, [line] * len(columns)))
            if d.pop():
                current_index = self._lines.index(line)
                self._lines = self._lines[current_index:]
                return True
        return False

    def parse_raw_column(self, event):
        col_offsets = {}
        col_order = OrderedDict()
        line = self._lines[0]
        for key, column in self._view.COLUMN.items():
            for result, start, end in pp.Literal(column).scanString(line):
                col_offsets[(start, end)] = result[0]
        user_defined_columns = copy.deepcopy(self._view.COLUMN)
        for key in sorted(col_offsets.iterkeys()):
            for x, y in self._view.COLUMN.items():
                if col_offsets[key] == user_defined_columns.get(x):
                    col_order[key] = x
                    user_defined_columns.pop(x)
                    break
        print col_order
        key = self._table.KEY
        if key not in self._view.COLUMN and key in self._view.COLUMN.values():
            for user_provided, from_table in self._view.COLUMN.items():
                if key == from_table:
                    key = user_provided
        items = re.split('\s\s+', self._lines[1])

        post_integer_data_types = map(is_integer, items)
        for line in self._lines[1:]:
            items = re.split('\s\s+', line)
            if len(items) == len(col_order):
                post_integer_data_types, pre_integer_data_types = \
                    map(is_integer, items), post_integer_data_types
                if post_integer_data_types == pre_integer_data_types:
                    items = map(lambda x, y: int(x) if y is True else x,
                                items, post_integer_data_types)
                    tmp_dict = dict(zip(col_order.values(), items))
                    self._data[tmp_dict[key]] = tmp_dict
                else:
                    break
            elif line.strip() == '':
                break
        return self._data



