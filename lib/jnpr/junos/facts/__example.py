# Import any exceptions raised in this module.
from jnpr.junos.exception import ConnectNotMasterError

# The name of this file should be based on the RPCs which are invoked in this
# file. This avoids accidentally inovking the same RPC multiple times when we
# could invoke it just once and gather multiple facts from the output.

# Must have a provide_facts() function
# Must return a tuple with string values
# Each fact that is handled/returned by this module.
def provides_facts():
    """
    Doc String details.
    Returns:

    """
    return ('foo','bar',)

# Must have a get_facts(device) function
# single mandatory device argument which is the corresponding Device object
# Must return a dictionary with a key for each
# fact that is handled/returned by this module.
# Should raise an appropriate exception if the response from the device prevents
# getting value(s) for ALL of the facts provided by this module. The example
# gets the 'foo' and 'bar' facts. An exception should only be raised if the
# error prevents getting the value for the 'foo' fact AND prevents getting
# the value for the 'bar' fact. If unable to determine the value for a
# given fact, then set the value for that fact to None.
def get_facts(device):
    """
    Doc String details.
    """
    # Invoke an RPC on device.
    # Try to avoid cli() or shell()
    # Try to avoid any RPC which requires more than view privileges
    # Try to avoid any RPC which doesn't run on non-master REs
    # Try to avoid any RPC which takes more than a couple of seconds to execute.
    # Definitely avoid any RPC which MIGHT take longer than the timeout.
    # If there are different ways of gathering the info depending on
    # Junos version, platform, model, or other things, then try the most common
    # way first, catch exceptions, try the second most common, etc.
    # Note that executing an RPC might itself raise an exception. There is no
    # need to catch that exception. It is handled within the FactCache() class.
    rsp = device.rpc.get_foo_bar_information()

    # Handle any exceptional situations unique to this RPC which prevent getting
    # values for ALL of the facts provided by this module.
    # These are examples which MAY or MAY NOT apply to your particular RPC.
    # Don't just blindly leave these in.
    if rsp.tag == 'error':
        raise RpcError()

    # An example of a boolean fact. False if the top-level tag is not 'foo'.
    foo = False
    if rsp.tag == 'foo':
         foo = True

    # An example of a string value which might be found at various levels or
    # locations within the response hierarchy.
    bar = (
        rsp.findtext('.//chassis[1]/bar') or
        rsp.findtext('.//chassis-module[name="Backplane"]/bar') or
        rsp.findtext('.//chassis-module[name="Midplane"]/bar'))

    return {'foo': foo,
            'bar': bar,}