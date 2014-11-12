import json
from lxml import etree


class TableJSONEncoder(json.JSONEncoder):
    """
    Used to encode Table/View instances into JSON.  See :meth:`Table.to_json`.
    """
    def default(self, obj):
        from jnpr.junos.factory.view import View
        from jnpr.junos.factory.table import Table

        if isinstance(obj, View):
            obj = dict(obj.items())
        elif isinstance(obj, Table):
            obj = dict((str(item.name), item) for item in obj)
        else:
            obj = super(TableJSONEncoder, self).default(obj)
        return obj


class TableViewJSONEncoder(json.JSONEncoder):
    """
    Used to encode Table/View instances into JSON.  See :meth:`Table.to_json`.
    """
    def default(self, obj):
        from jnpr.junos.factory.view import View
        from jnpr.junos.factory.table import Table

        if isinstance(obj, View):
            obj = {str(obj.name): dict(obj.items())}
        elif isinstance(obj, Table):
            obj = dict((str(item.name), dict(item.items())) for item in obj)
        else:
            obj = super(TableViewJSONEncoder, self).default(obj)
        return obj


class PyEzJSONEncoder(json.JSONEncoder):
    """
    Used to encode facts and rpc instances into JSON.`.
    """
    def default(self, obj):
        from jnpr.junos.facts.swver import version_info
        if isinstance(obj, version_info):
            obj = obj.v_dict
        elif isinstance(obj, etree._Element):
            def recursive_dict(element):
                return element.tag, dict(map(recursive_dict, element)) or element.text
            _, obj = recursive_dict(obj)
        else:
            obj = super(PyEzJSONEncoder, self).default(obj)
        return obj
