import json

class TableJSONEncoder( json.JSONEncoder ):
    """
    Used to encode Table/View instances into JSON.  See :meth:`Table.to_json`.
    """
    def default(self, obj):
        from jnpr.junos.factory.view import View
        from jnpr.junos.factory.table import Table

        if isinstance(obj, View):
            obj = dict(obj.items())
        elif isinstance(obj,Table):
            obj = { item.name: item for item in obj }
        else:
            obj = super(TableJSONEncoder, self).default(obj)
        return obj

class TableViewJSONEncoder( json.JSONEncoder ):
    """
    Used to encode Table/View instances into JSON.  See :meth:`Table.to_json`.
    """
    def default(self, obj):
        from jnpr.junos.factory.view import View
        from jnpr.junos.factory.table import Table

        if isinstance(obj, View):
            obj = { obj.name: dict(obj.items()) }
        elif isinstance(obj,Table):
            obj = { item.name: dict(item.items()) for item in obj }
        else:
            obj = super(TableViewJSONEncoder, self).default(obj)
        return obj
