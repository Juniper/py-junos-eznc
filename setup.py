import os
import sys

sys.path.insert(0,'lib')
from setuptools import setup, find_packages

setup(
    name = "junos-eznc",
    namespace_packages = ['jnpr'],
    version = "0.0.2",
    author = "Jeremy Schulman",
    author_email = "jschulman@juniper.net",
    description = ( "Junos 'EZ' automation for non-programmers" ),
    license = "BSD-2",
    keywords = "Junos NETCONF networking automation",
    url = "http://www.github.com/jeremyschulman/py-junos-eznc",
    package_dir={'':'lib'},    
    packages=find_packages('lib'),
    package_data={'jnpr.junos.op': ['*.yml']},
    install_requires=[
        "netaddr",
        "lxml",
        "jinja2",
        "scp"
    ],
)
