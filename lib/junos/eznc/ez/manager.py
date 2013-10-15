# ez/manager.py
# stdlib
from inspect import isclass

# package modules
from ..resources import Resource 

import pdb

class Manager(object):
  """
    Manager is a metaprogramming object that allows a programmer
    to bind helper functions to a :Netconf: object :ez: attribute.  
    Each :Manager: maintains a list of helper functions and a list of 
    child :Manager: objects.  In this way, a :Manager: can provide a
    hierarchy of helpers
  """

  def __init__(self, junos, **kvargs ):
    """
    """
    self._junos = junos
    self._items = {}
    self._children = {}

  ##### -----------------------------------------------------------------------
  ##### internal operations
  ##### -----------------------------------------------------------------------

  def _get(self, name):
    """
      retrieves a the helper function by name
    """
    return self._items.get(name)

  def _set(self, name, item ):
    """
      add a named item
    """
    self._items[name] = item
    return item

  def _load( self, items ):    
    """
      binds a dictonary of name/helpers
    """
    for name, item in items.items():
      self._set( name, item )

  def _append( self, name, thing=None ):
    """
      append a child by :name: to this :Manager:

      if :thing: is provided, it is a list of functions to load into
      the newly created child manager 
    """
    new_mgr = self.__class__(self._junos)
    if len(thing): new_mgr._load( thing )
    self._children[name] = new_mgr
    return new_mgr

  ##### -----------------------------------------------------------------------
  ##### PROPERTIES
  ##### -----------------------------------------------------------------------

  @property
  def items(self):
    """
      returns a list of child names
    """
    return self._items.keys() + self._children.keys()

  ##### -----------------------------------------------------------------------
  ##### OPERATOR OVERLOADING
  ##### -----------------------------------------------------------------------

  def __getattr__( self, name ):
    """
      invoke the :name: of the thing within :Manager:
    """

    # first see if this is a child, and if so,
    # return that for further processing

    if name in self._children:
      return self._children[name]

    # ok, so not a child, see if we know
    # about this method request

    method_fn = self._get( name )

    # if this helper doesn't know about the
    # request method, then return a function
    # that will raise an AttributeError

    if not method_fn: 
      def _no_method_fn(*vargs, **kvargs):
        raise AttributeError("Unknown ez helper: '%s'" % name)
      return _no_method_fn

    # otherwise, return a closure that will in turn
    # invoke the helper function passing the associated
    # WLC object and called arguments

    def _helper_fn(*vargs, **kvargs):
      return method_fn(self._junos, vargs, **kvargs)

    # cleverly metabind the function help, yo! 
    _helper_fn.__doc__ = method_fn.__doc__
    _helper_fn.__name__ = method_fn.__name__

    # return the function for later execution
    return _helper_fn

  ##### -----------------------------------------------------------------------
  ##### CALLABLE
  ##### -----------------------------------------------------------------------

  def __call__(self, *vargs, **kvargs ):
    """
    Entry point for adding things to the :Manager:

    ( dict ):
    Adds a list of name=<function> items to the :Manager: items

    ( name=<function> ):
    Adds the function to the :Manager: items

    ( name=<dictionary> ):
    Adds a new child :name: and loads the dictionary of functions

    ( name=<Resource>):
    Adds an instance of the :Resource: to the :Manager:
    """

    ##### check vargs first ... 

    if vargs:
      if isinstance(vargs[0], dict):
        # a dict is a collection of callables, i.e. a named
        # list of helper functions
        self._load( vargs[0] )
        return self

    ##### processing kvargs now ...

    name, thing = next(kvargs.iteritems())

    if isclass(thing):
      if issubclass(thing, Resource):
        # then we're adding a Resource manager object
        new_inst = thing(self._junos)
        self._items[name] = new_inst
        self.__dict__[name] = new_inst
        return self

    if isinstance( thing, dict ):
      # then this a dictionary of name=<function> and we want to
      # Append it to this :Manager:
      self._append( name, thing )
      return self

    if callable( thing ):
      # a callable thing is means we just want to add it
      self._set(name, thing)
      return self

    # if we're here, then we've got a problem
    raise ValueError, "Don't know what to do with: %s" % name