import os
import sys

from setuptools import setup, find_packages
from pip.req import parse_requirements

requirements = [str(x.req) for x in parse_requirements('requirements.txt')]

setup(
    name="junos-eznc",
    namespace_packages=['jnpr'],
    version="0.1.1",
    author="Jeremy Schulman",
    author_email="jschulman@juniper.net",
    description=("Junos 'EZ' automation for non-programmers"),
    license = "Apache 2.0",
    keywords = "Junos NETCONF networking automation",
    url = "http://www.github.com/Juniper/py-junos-eznc",
    package_dir={'': 'lib'},
    packages=find_packages('lib'),
    package_data={
        'jnpr.junos.op': ['*.yml'],
        'jnpr.junos.cfgro': ['*.yml']
    },
    install_requires=requirements,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Other Scripting Engines',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Topic :: System :: Networking :: Firewalls',
        'Topic :: Text Processing :: Markup :: XML'
    ],
)
