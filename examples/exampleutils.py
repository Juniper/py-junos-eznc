from lxml.builder import E 
from lxml import etree

def ppxml(r): print etree.tostring(r,pretty_print=True)