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

DEL = {'delete': 'delete'}            # Junos XML resource delete
REN = {'rename': 'rename'}            # Junos XML resource rename

def NAME(name): return { 'name': name }
def INSERT(cmd): return {'insert': cmd}

BEFORE = {'insert': 'before'}
AFTER = {'insert': 'after'}

# used with <get-configuration> to load only the object identifiers and 
# not all the subsequent configuration

NAMES_ONLY = {'recurse': "false"}