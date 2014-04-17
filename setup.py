import os
import sys

# sys.path.insert(0,'lib')
from setuptools import setup, find_packages
#import pkg_resources

requirements = ['ncclient >= 0.4.1', 'netaddr',
                'jinja2 >= 2.7.1', 'lxml >= 3.2.4',
                'scp >= 0.7.0', 'PyYAML >= 3.10']

setup(
    name="junos-eznc",
    namespace_packages=['jnpr'],
    version="0.1.0",
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
        'Development Status :: 3 - Alpha',
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
