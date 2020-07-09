# Import any exceptions raised in this module.
from jnpr.junos.exception import RpcError


# In general, a "fact" should be a piece of information that does not change
# over the life of a PyEZ connection. While things like mastership state can
# change, they also result in the PyEZ connection being closed, so it can
# be considered a fact. Things like number of routes in the route table or
# system uptime do not maintain the same value over the life of a PyEZ
# connection and should therefore not be considered facts.

# The name of this file should be based on the RPCs which are invoked by this
# file. This avoids accidentally invoking the same RPC multiple times when we
# could invoke it just once and gather multiple facts from the output.

# An import for each fact file must be present in
# lib/jnpr/junos/facts/__init__.py

# The file must include a provide_facts() function
# The provide_facts() function must return a dictionary. The keys of the
# dictionary are each fact that is handled/returned by this module. The value
# of each item in the dictionary is the documentation string describing the
# particular fact.
def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {
        "foo": "The foo information.",
        "bar": "The bar information.",
    }


# The file must include a get_facts(device) function. The get_facts(device)
# function takes a single mandatory device argument which is the Device object
# on which the fact is discovered.
# The get_facts(device) function must return a dictionary with a key for each
# fact that is handled/returned by this module.
# The get_facts(device) function should raise an appropriate exception if the
# response from the device prevents getting value(s) for ALL of the facts
# provided by the module. The example gets the 'foo' and 'bar' facts.
# An exception should only be raised if the error prevents getting the value
# for the 'foo' fact AND prevents getting the value for the 'bar' fact. If
# unable to determine the value for a given fact, then set the value for that
# fact to None.
def get_facts(device):
    """
    Gathers facts from the <get-foo-bar-information/> RPC.
    """
    # Invoke an RPC on device using device.rpc.rpc_name() methods.
    # Avoid using the cli() or shell() methods.
    # Avoid any RPC which requires more than view privileges.
    # Avoid any RPC which doesn't run on non-master REs.
    # Avoid any RPC which takes more than a couple of seconds to execute.
    # Avoid any RPC which MIGHT take longer than the default PyEZ RPC timeout
    # (currently 30 seconds).
    # If there are different ways of gathering the info depending on
    # Junos version, platform, model, or other things, then try the most common
    # way first, catch exceptions, try the second most common, etc.
    # Note that executing an RPC might itself raise an exception. There is no
    # need to catch that exception. It is handled within the FactCache() class.
    # Always pass the normalize=True argument when invoking an RPC to avoid any
    # potential white-space problems in the RPC response.
    rsp = device.rpc.get_foo_bar_information(normalize=True)

    # Handle any exceptional situations unique to this RPC which prevent
    # getting values for ALL of the facts provided by this module.
    # These are examples which MAY or MAY NOT apply to your particular RPC.
    # Don't just blindly leave these in.
    if rsp.tag == "error":
        raise RpcError()

    # An example of a boolean fact. False if the top-level tag is not 'foo'.
    foo = False
    if rsp.tag == "foo":
        foo = True

    # An example of a string value which might be found at various levels or
    # locations within the response hierarchy.
    bar = (
        rsp.findtext(".//chassis[1]/bar")
        or rsp.findtext('.//chassis-module[name="Backplane"]/bar')
        or rsp.findtext('.//chassis-module[name="Midplane"]/bar')
    )

    return {
        "foo": foo,
        "bar": bar,
    }
