# jxml.py

"""
  These are Junos XML 'helper' definitions use for generic XML processing

  .DEL to delete an item
  .REN to rename an item, requires the use of NAME()

  .INSERT(<'before'|'after'>) to reorder an item, requires the use of NAME()
  .BEFORE to reorder an item before another, requires the use of NAME()
  .AFTER to reorder an item after another, requires the use of NAME()

  .NAME(name) to assign the name attribute

"""

DEL = {'delete': 'delete'}              # Junos XML resource delete
REN = {'rename': 'rename'}              # Junos XML resource rename
ACTIVATE = {'active': 'active'}         # activate resource
DEACTIVATE = {'inactive': 'inactive'}   # deactivate resource
REPLACE = {'replace': 'replace'}         # replace elements


def NAME(name):
    return {'name': name}


def INSERT(cmd):
    return {'insert': cmd}

BEFORE = {'insert': 'before'}
AFTER = {'insert': 'after'}

# used with <get-configuration> to load only the object identifiers and
# not all the subsequent configuration

NAMES_ONLY = {'recurse': "false"}

# for <get-configuration>, attributes to retrieve from apply-groups
INHERIT = {'inherit': 'inherit'}
INHERIT_GROUPS = {'inherit': 'inherit', 'groups': 'groups'}
INHERIT_DEFAULTS = {'inherit': 'defaults', 'groups': 'groups'}


def remove_namespaces(xml):
    for elem in xml.getiterator():
        i = elem.tag.find('}')
        if i > 0:
            elem.tag = elem.tag[i + 1:]
    return xml


def rpc_error(rpc_xml):
    """
      extract the various bits from an <rpc-error> element
      into a dictionary
    """
    remove_namespaces(rpc_xml)

    if 'rpc-reply' == rpc_xml.tag:
        rpc_xml = rpc_xml[0]

    def find_strip(x):
        ele = rpc_xml.find(x)
        return ele.text.strip() if None != ele else None

    this_err = {}
    this_err['severity'] = find_strip('error-severity')
    this_err['source'] = find_strip('source-daemon')
    this_err['edit_path'] = find_strip('error-path')
    this_err['bad_element'] = find_strip('error-info/bad-element')
    this_err['message'] = find_strip('error-message')

    return this_err
