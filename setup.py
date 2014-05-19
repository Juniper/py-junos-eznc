from setuptools import setup, find_packages

# parse requirements
req_lines = [line.strip() for line in open(
    'requirements.txt').readlines()]
install_reqs = list(filter(None, req_lines))

setup(
    name="junos-eznc",
    namespace_packages=['jnpr'],
    version="0.2.0",
    author="Jeremy Schulman",
    author_email="jschulman@juniper.net",
    description=("Junos 'EZ' automation for non-programmers"),
    license="Apache 2.0",
    keywords="Junos NETCONF networking automation",
    url="http://www.github.com/Juniper/py-junos-eznc",
    package_dir={'': 'lib'},
    packages=find_packages('lib'),
    package_data={
        'jnpr.junos.op': ['*.yml'],
        'jnpr.junos.cfgro': ['*.yml']
    },
    install_requires=install_reqs,
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
