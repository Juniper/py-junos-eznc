class RunstatMakerViewFields(object):
  """
  Used to dynamically create a field dictionary used with the 
  RunstatView class
  """
  def __init__(self):
    self._fields = dict()

  def _prockvargs(self, field, name, **kvargs):
    if not len(kvargs): return
    field[name].update(kvargs)

  @property
  def end(self):
    return self._fields

  def str(self, name, xpath=None, **kvargs):
    """ field is a string """
    if xpath is None: xpath=name
    field = {name:{'xpath': xpath}}
    self._prockvargs( field, name, **kvargs )
    self._fields.update(field)
    return self

  def astype(self,name,xpath=None, as_type=int, **kvargs):
    """ field is of type <as_type> provided by caller """
    if xpath is None: xpath=name    
    field = {
      name: {'xpath': xpath, 'as_type': as_type }
    }
    self._prockvargs(field,name,**kvargs)
    self._fields.update( field )
    return self

  def int(self,name,xpath=None,**kvargs):
    """ field is an integer """
    return self.astype(name,xpath, int, **kvargs)

  def flag(self,name,xpath=None,**kvargs):
    """ 
    field is a flag, results in True/False if the xpath element exists or not 
    model this as a boolean type <bool>
    """
    return self.astype(name,xpath,bool,**kvargs)

  def table(self, name, table ):
    """ field is a RunstatTable """
    self._fields.update({
      name: {'table': table }
    })
    return self
