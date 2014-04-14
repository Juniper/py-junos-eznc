# resources/srx/addrbook_finder.py
import netaddr

#from .zone import Zone
#from .addrbook import ZoneAddrBook


class AddrBookFinderResults(object):

    """
    Helper-class to hold the results of a :ZoneAddrFind.find(): invocation
    """

    def __init__(self, ab, find, results):
        self._ab = ab
        self._find = find
        self._results = results
        self.sets = []

    @property
    def lpm(self):
        """
        The longest-prefix-matching address is the last one in the results
        list. This fact is a result of the :ZoneAddrFinder.find(): sorted call
        """
        return self._results[-1][0]

    @property
    def items(self):
        """
        Return a list of the matching address items and sets
        """
        return self.addrs + self.sets

    @property
    def addrs(self):
        """
        Return a list of the matching address items
        """
        # return a list of names
        return [x[0] for x in self._results]

    @property
    def matching(self):
        """
        Returns the string value of the original querried address presented to
        the find() method
        """
        return self._find

    def __repr__(self):
        """
        Provides the matching value and the zone name associated with this
        results
        """
        return "%s(%s in %s)" % (
            self.__class__.__name__, self._find, self._ab.name)


class AddrBookFinder(object):

    # -------------------------------------------------------------------------
    # CONSTRUCTOR
    # -------------------------------------------------------------------------

    def __init__(self, addr_book):
        """
        addr_book
          Either a ZoneAddrBook or SharedAddrBook instance
        """
        self._ab = addr_book
        self._index = None

    def __repr__(self):
        return "AddrBookFinder(%s)" % self._ab.name

    def compile(self):
        """
        Compile a list of netaddr objects against the catalog of address items
        """
        # create a tuple of (addr-name, netaddr) for each of the items in the
        # address-book
        self._index = [(name, netaddr.IPNetwork(addr['ip_prefix']))
                       for name, addr in self._ab.addr.catalog.items()]

    def find(self, addr, sets=True):
        """
        Given an ip or ip_prefix locate the matching address book address
        and address-set items.
        """

        # if the caller hasn't explicity invoked :compile(): to create the
        # netaddr objects, then do that now.

        if self._index is None:
            self.compile()

        # convert the provided :addr: into a netaddr object and then
        # to a subnet match to find address entries.  the matching
        # values will be sorted with longest prefix matching to be
        # last in the list

        ip = netaddr.IPNetwork(addr).ip
        # is ip in the subnet?
        in_net = lambda i: ip & i[1].netmask == i[1].network
        # used to sort by prefix-length
        by_pflen = lambda a, b: cmp(a[1].prefixlen, b[1].prefixlen)
        r = sorted(
            filter(
                in_net,
                self._index),
            cmp=by_pflen)               # find/sort
        if r is None:
            return None

        # now that we have some matching entries, we should find which
        # address-set items uses the items

        results = AddrBookFinderResults(self._ab, addr, r)
        if sets is True:
            results.sets = self.find_sets(results)

        # return the results object
        return results

    def find_sets(self, r):
        """
        Given a :AddrBookFinderResults: object, which contains the list of
        matching address items, locate the list of address-set objects that
        use those items
        """
        catalog = self._ab.set.catalog
        in_addr = lambda i: i in v['addr_list']
        sets = [k for k, v in catalog.items() if filter(in_addr, r.addrs)]
        in_set = lambda i: i in v['set_list']
        subsets = [k for k, v in catalog.items() if filter(in_set, sets)]
        return sets + subsets
