from setuptools import setup, find_packages
import versioneer
import os

# Install customer paramiko
os.system("pip install git+https://github.com/Juniper/paramiko.git@v3.4.0-JNPR")
# parse requirements
req_lines = [line.strip() for line in open("requirements.txt").readlines()]
install_reqs = list(filter(None, req_lines))

setup(
    name="junos-eznc",
    namespace_packages=["jnpr"],
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="Jeremy Schulman, Nitin Kumar, Rick Sherman, Stacy Smith",
    author_email="jnpr-community-netdev@juniper.net",
    description=("Junos 'EZ' automation for non-programmers"),
    license="Apache 2.0",
    keywords="Junos NETCONF networking automation",
    url="http://www.github.com/Juniper/py-junos-eznc",
    package_dir={"": "lib"},
    packages=find_packages("lib"),
    package_data={
        "jnpr.junos.op": ["*.yml"],
        "jnpr.junos.command": ["*.yml"],
        "jnpr.junos.cfgro": ["*.yml"],
        "jnpr.junos.resources": ["*.yml"],
    },
    python_requires=">=3.8",
    install_requires=install_reqs,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Telecommunications Industry",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
        "Topic :: Text Processing :: Markup :: XML",
    ],
)
