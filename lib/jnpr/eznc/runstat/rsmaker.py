from pdb import set_trace

from .view import RunstatView
from .table import RunstatTable

class RunstatMaker(object):

  @classmethod
  def View(cls, cls_name=None, fields=None):
    """
    :name: name of new class object
    :field: dictionary of fields
    """
    if cls_name is None: cls_name = 'RunstatView'
    new_cls = type(cls_name, (RunstatView,), {})
    new_cls.FIELD_XPATH = fields
    new_cls.__module__ = __name__
    return new_cls

  @classmethod
  def TableRpc(cls,cls_name,get):
    new_cls = type(cls_name, (RunstatTable,), {} )
    new_cls.GET_RPC = get['rpc_cmd']
    new_cls.GET_ARGS = get.get('rpc_arg', {})
    new_cls.ITER_XPATH = get['item']
    new_cls.NAME_XPATH = get.get('name',RunstatTable.NAME_XPATH)
    new_cls.VIEW = get.get('view')
    new_cls.__module__ = __name__
    return new_cls

  @classmethod
  def Table(cls,cls_name=None, item=None, name='name',view=None):
    if cls_name is None: cls_name = 'RunstatTable'
    new_cls = type(cls_name, (RunstatTable,), {} )
    new_cls.ITER_XPATH = item
    new_cls.NAME_XPATH = name
    new_cls.VIEW = view
    new_cls.__module__ = __name__
    return new_cls

