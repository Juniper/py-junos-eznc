import os
import jinja2

_J2LDR = jinja2.Environment(
  trim_blocks=True,
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)+'/templates'))