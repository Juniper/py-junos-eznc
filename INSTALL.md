### Installation

I am currently in the process of building a "proper" setup.py file.  In the meantime, please bear with me.

To install this module, you will first need to download and install the [ncclient](https://github.com/juniper/ncclient) module from the Juniper github repo directly.  Follow the instructions there for details.

Once you've done that, you can then install this module using:

````shell
[py-junos-eznc] python setup.py install
````

Once you've done that you should be able to verify the installation via the python shell:

````python
import jnpr.eznc

print jnpr.eznc.VERSION
````

