"""
  facts['HOME'] = login home directory
"""
from lxml.builder import E

def facts_session(dev, facts):
    facts['HOME'] = dev.rpc(
        E.command("show cli directory")).findtext('./working-directory')
