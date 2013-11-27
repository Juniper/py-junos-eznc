from os.path import dirname,join
from .yaml import loadyaml

# import the definitions from the YAML file in this directory and
# make them part of this module, yo!

for each in loadyaml(join(dirname(__file__),'routes.yml')):
  globals()[each.__name__] = each
