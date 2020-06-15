from setuptools import setup, find_packages
import sys
import versioneer

# parse requirements
req_lines = [line.strip() for line in open("requirements.txt").readlines()]
install_reqs = list(filter(None, req_lines))

# refer: https://github.com/Juniper/py-junos-eznc/issues/1015
# should be removed when textfsm releases >=1.1.1
if sys.platform == "win32":
    if "ntc_templates" in install_reqs:
        install_reqs.remove("ntc_templates")
        install_reqs.append("ntc_templates==1.4.1")
    install_reqs.append("textfsm==0.4.1")

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
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
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
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
        "Topic :: Text Processing :: Markup :: XML",
    ],
)
