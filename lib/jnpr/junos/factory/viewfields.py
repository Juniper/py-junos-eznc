class ViewFields(object):

    """
    Used to dynamically create a field dictionary used with the
    RunstatView class
    """

    def __init__(self):
        self._fields = dict()

    def _prockvargs(self, field, name, **kvargs):
        if not len(kvargs):
            return
        field[name].update(kvargs)

    @property
    def end(self):
        return self._fields

    def str(self, name, xpath=None, **kvargs):
        """field is a string"""
        if xpath is None:
            xpath = name
        field = {name: {"xpath": xpath}}
        self._prockvargs(field, name, **kvargs)
        self._fields.update(field)
        return self

    def astype(self, name, xpath=None, astype=int, **kvargs):
        """
        field string value will be passed to function :astype:

        This is typically used to do simple type conversions,
        but also works really well if you set :astype: to
        a function that does a basic converstion like look
        at the value and change it to a True/False.  For
        example:

          astype=lambda x: True if x == 'enabled' else False
        """
        if xpath is None:
            xpath = name
        field = {name: {"xpath": xpath, "astype": astype}}
        self._prockvargs(field, name, **kvargs)
        self._fields.update(field)
        return self

    def int(self, name, xpath=None, **kvargs):
        """field is an integer"""
        return self.astype(name, xpath, int, **kvargs)

    def flag(self, name, xpath=None, **kvargs):
        """
        field is a flag, results in True/False if the xpath element exists or
        not. Model this as a boolean type <bool>
        """
        return self.astype(name, xpath, bool, **kvargs)

    def group(self, name, xpath=None, **kvargs):
        """
        field is an apply group, results in value of group attr if the xpath
        element has the associated group attribute.
        """
        xpath = "./{}/@group".format(xpath)
        return self.astype(name, xpath, str, **kvargs)

    def table(self, name, table):
        """field is a RunstatTable"""
        self._fields.update({name: {"table": table}})
        return self
