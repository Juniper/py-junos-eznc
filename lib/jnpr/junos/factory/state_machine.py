from transitions import Machine
import pyparsing as pp
from collections import OrderedDict
import re


class StateMachine(Machine):

    def __init__(self, table_view):
        self._table = table_view
        self._view = self._table.VIEW
        self._lines = []
        self.states = ['column', 'row_column', 'gas', 'plasma']
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
        # reverse column dictionary (python 2.7+ compatible code)
        reverse_columns = {val: key for key, val in self._view.COLUMN.items()}
        for key in sorted(col_offsets.iterkeys()):
            col_order[key] = reverse_columns[col_offsets[key]]
        key = self._table.KEY
        if key in self._view.COLUMN.values():
            key = reverse_columns[key]
        for line in self._lines[1:]:
            items = re.split('\s\s+', line)
            if len(items) == len(col_order):
                tmp_dict = dict(zip(col_order.values(), items))
                self._data[tmp_dict[key]] = tmp_dict
        return self._data



