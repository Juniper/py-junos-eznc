from pdb import set_trace

from .view import RunstatView
from .table import RunstatTable

class RunstatMaker(object):

  @classmethod
  def View(cls, fields, view_name=None, ):
    """
    :name: name of new class object
    :field: dictionary of fields
    """
    if view_name is None: view_name = 'RunstatView'
    new_cls = type(view_name, (RunstatView,), {})
    new_cls.FIELDS = fields
    new_cls.__module__ = __name__
    return new_cls

  @classmethod
  def TableGetter(cls, cmd, args=None, item=None, key=RunstatTable.NAME_XPATH, view=None, getter_name=None ):
    if getter_name is None: getter_name = "RunstatTableGetter." + cmd
    new_cls = type(getter_name, (RunstatTable,), {} )
    new_cls.GET_RPC = cmd
    new_cls.GET_ARGS = args or {}
    new_cls.ITER_XPATH = item
    new_cls.NAME_XPATH = key 
    new_cls.VIEW = view
    new_cls.__module__ = __name__
    return new_cls

  @classmethod
  def Table(cls, item, key=RunstatTable.NAME_XPATH, view=None, table_name=None):
    if table_name is None: table_name = 'RunstatTable.' + item
    new_cls = type(table_name, (RunstatTable,), {} )
    new_cls.ITER_XPATH = item
    new_cls.NAME_XPATH = key 
    new_cls.VIEW = view
    new_cls.__module__ = __name__
    return new_cls

