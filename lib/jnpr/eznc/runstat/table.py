from lxml import etree

class RunstatTable(object):
  NAME_XPATH = 'name'

  def __init__(self,ncdev):
    self._ncdev = ncdev
    self._xml_got = None

  @property
  def N(self):
    return self._ncdev

  @property
  def R(self):
    return self._ncdev.rpc

  @property
  def got(self):
    return self._xml_got

  def assert_data(self):
    if self._xml_got is None: raise RuntimeError("No data")

  def get(self, **kvargs):
    args = {}
    args.update(self.GET_ARGS)
    args.update(kvargs)
    self._xml_got = getattr(self.R,self.GET_RPC)(**args)

  def keys(self):
    return [n.findtext(self.NAME_XPATH).strip() for n in iter(self)]

  def __len__(self):
    return len(self.keys())

  def __getitem__(self,value):
    """ select a specific item by value (name) and return the XML """
    self.assert_data()
    xpath = self.ITER_XPATH + '[normalize-space(%s)="' % self.NAME_XPATH + value + '"]'
    found = self.got.xpath(xpath)
    return found[0] if len(found) else None

  def __iter__(self):
    """ iteratable of each toplevel xpath item """
    self.assert_data()
    return iter(self.got.xpath(self.ITER_XPATH))

  def __repr__(self):
    return "%s(%s)" % (self.__class__.__name__, self.N.hostname)
