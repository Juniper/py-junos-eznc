import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "junos-eznc",
    version = "0.0.1",
    author = "Jeremy Schulman",
    author_email = "jschulman@juniper.net",
    description = ( "Making Junos automation via NETCONF 'easy'" ),
    license = "BSD-2",
    keywords = "Junos NETCONF",
    url = "http://www.github.com/jeremyschulman/py-junos-eznc",
    packages=find_packages('lib'),
    package_dir={'':'lib'}
)
