import os
import sys

sys.path.insert(0,'lib')
from setuptools import setup, find_packages
from jnpr.eznc import VERSION

setup(
    name = "junos-eznc",
    version = VERSION,
    author = "Jeremy Schulman",
    author_email = "jschulman@juniper.net",
    description = ( "Making Junos automation via NETCONF 'easy'" ),
    license = "BSD-2",
    keywords = "Junos NETCONF",
    url = "http://www.github.com/jeremyschulman/py-junos-eznc",
    packages=find_packages('lib'),
    package_dir={'':'lib'}
)
