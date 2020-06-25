# 3rd-party modules
from lxml.builder import E

# local module
from jnpr.junos.cfg import Resource
from jnpr.junos import jxml as JXML


class UserSSHKey(Resource):

    """
    [edit system login user <name> authentication <key-type> <key-value> ]

    Resource name: tuple(<key-type>, <key-value>)
      <key-type> : ['ssh-dsa', 'ssh-rsa']
      <key-value> : SSH public key string (usually something very long)

    Resource manager utilities:
      load_key - allows you to load an ssh-key from a file or str
    """

    # there are no properties, since the name <key-value> constitutes the
    # actual ssk key data, yo!

    PROPERTIES = []

    # -----------------------------------------------------------------------
    # XML readers
    # -----------------------------------------------------------------------

    def _xml_at_top(self):
        key_t, key_v = self._name
        return E.system(
            E.login(
                E.user(E.name(self.P.name), E.authentication(E(key_t, E.name(key_v))))
            )
        )

    def _xml_at_res(self, xml):
        return xml.find(".//authentication/%s" % self._name[0])

    def _xml_to_py(self, has_xml, has_py):
        Resource._r_has_xml_status(has_xml, has_py)

    # -----------------------------------------------------------------------
    # UTILITY FUNCTIONS
    # -----------------------------------------------------------------------

    def load_key(self, path=None, key_value=None):
        """
        Adds a new ssh-key to the user authentication.  You can
        provide either the path to the ssh-key file, or the contents
        of they key (useful for loading the same key on many devices)

        :path: (optional)
          path to public ssh-key file on the local server,

        :key_value: (optional)
          the contents of the ssh public key
        """

        if not self.is_mgr:
            raise RuntimeError("must be a resource-manager!")

        if path is None and key_value is None:
            raise RuntimeError("You must provide either path or key_value")

        if path is not None:
            # snarf the file into key_value, yo!
            with open(path, "r") as f:
                key_value = f.read().strip()

        # extract some data from the key value, this will either
        # be 'ssh-rsa' or 'ssh-dss'.  we need to decode this to set
        # the type correctly in the RPC.

        vt = key_value[0:7]
        key_map = {"ssh-rsa": "ssh-rsa", "ssh-dss": "ssh-dsa"}
        key_type = key_map.get(vt)
        if key_type is None:
            raise RuntimeError("Unknown ssh public key file type: %s" % vt)

        # at this point we are going to add a new key, so really what we are
        # doing is accessing a new instance of this class and
        # doing a write, but just a touch since there are no properties, yo!

        new_key = self[(key_type, key_value)]
        return new_key.write(touch=True)

    # -----------------------------------------------------------------------
    # Manager List, Catalog
    # -----------------------------------------------------------------------

    def _r_list(self):
        # the key list comes from the parent object.
        self._rlist = self.P["$sshkeys"]

    def _r_catalog(self):
        # no catalog but the keys
        self._rcatalog = dict((k, None) for k in self.list)
