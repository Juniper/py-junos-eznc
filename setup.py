from setuptools import setup, find_packages
import sys

# parse requirements
req_lines = [line.strip() for line in open(
    'requirements.txt').readlines()]
install_reqs = list(filter(None, req_lines))
if sys.version_info[:2] == (2, 6):
    install_reqs.append('importlib>=1.0.3')

setup(
    name="junos-eznc",
    namespace_packages=['jnpr'],
    version="2.1.3",
    author="Jeremy Schulman, Nitin Kumar, Rick Sherman, Stacy Smith",
    author_email="jnpr-community-netdev@juniper.net",
    description=("Junos 'EZ' automation for non-programmers"),
    license="Apache 2.0",
    keywords="Junos NETCONF networking automation",
    url="http://www.github.com/Juniper/py-junos-eznc",
    package_dir={'': 'lib'},
    packages=find_packages('lib'),
    package_data={
        'jnpr.junos.op': ['*.yml'],
        'jnpr.junos.cfgro': ['*.yml'],
        'jnpr.junos.resources': ['*.yml']
    },
    install_requires=install_reqs,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Topic :: Text Processing :: Markup :: XML'
    ],
)
