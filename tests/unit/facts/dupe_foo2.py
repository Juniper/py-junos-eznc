def provides_facts():
    """
    Returns a dictionary keyed on the facts provided by this module. The value
    of each key is the doc string describing the fact.
    """
    return {'foo': 'The foo information.'}

def get_facts(device):
    return {'foo': None }
