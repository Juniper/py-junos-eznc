import glob
import json
import yaml
import os.path

from jnpr.junos.factory.factory_loader import FactoryLoader

__all__ = ['load', 'loadjson', 'loadyaml', 'FactoryLoader']


def load(path):
    """
    Load a file at :path: that contains Table and View definitions.
    Returns a <dict> of item-name anditem-class definition.
    Supports both json and yaml natively; prefers JSON.
    In this way additional support can be added (csv, xml, etc)

    If you want to import these definitions directly into your namespace,
    (like a module) you would do the following:

      globals().update( load( <path-to-file> ))

    If you did not want to do this, you can access the items as the <dict>.
    For example, if your file contained a Table called MyTable, then
    you could do something like:

      catalog = load( <path-to-file> )
      MyTable = catalog['MyTable']

      table = MyTable(dev)
      table.get()
      ...
    """
    ext = os.path.splitext(path)[1]
    if ext == '':
        # We don't have an ext, find it
        candidates = glob.glob(path + '*')
        for candy in candidates:
            candy_ext = os.path.splitext(candy)[1]
            if candy_ext == '.yml' or candy_ext = '.yaml':
                return loadyaml(candy)
            else:
                return loadjson(candy)
    elif ext == '.yml' or ext == '.yaml':
        return loadyaml(path)
    else:
        return loadjson(path)

def loadyaml(path):
    # if no extension is given, default to '.yml'
    if os.path.splitext(path)[1] == '':
        path += '.yml'
    return FactoryLoader().load(yaml.load(open(path, 'r')))

def loadjson(path):
    # if no extension is given, default to '.json'
    if os.path.splitext(path)[1] == '':
        path += '.json'
    return FactoryLoader().load(json.load(open(path, 'r')))
