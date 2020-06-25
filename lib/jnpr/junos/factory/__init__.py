import yaml
import os.path

from jnpr.junos.factory.factory_loader import FactoryLoader

__all__ = ["loadyaml", "FactoryLoader"]


def loadyaml(path):
    """
    Load a YAML file at :path: that contains Table and View definitions.
    Returns a <dict> of item-name anditem-class definition.

    If you want to import these definitions directly into your namespace,
    (like a module) you would do the following:

      globals().update( loadyaml( <path-to-yaml-file> ))

    If you did not want to do this, you can access the items as the <dict>.
    For example, if your YAML file contained a Table called MyTable, then
    you could do something like:

      catalog = loadyaml( <path-to-yaml-file> )
      MyTable = catalog['MyTable']

      table = MyTable(dev)
      table.get()
      ...
    """
    # if no extension is given, default to '.yml'
    if os.path.splitext(path)[1] == "":
        path += ".yml"
    return FactoryLoader().load(yaml.load(open(path, "r"), Loader=yaml.FullLoader))
