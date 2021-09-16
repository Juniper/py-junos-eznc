# stdlib
from functools import wraps
import re
import sys

from lxml import etree
from ncclient.operations.rpc import RPCError
from ncclient.xml_ import NCElement
from jnpr.junos import jxml as JXML


def timeoutDecorator(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "dev_timeout" in kwargs:
            try:
                dev = args[0].dev
            except:
                dev = args[0]
            restore_timeout = dev.timeout
            dev.timeout = kwargs.pop("dev_timeout", None)
            try:
                result = function(*args, **kwargs)
                dev.timeout = restore_timeout
                return result
            except Exception:
                dev.timeout = restore_timeout
                raise
        else:
            try:
                return function(*args, **kwargs)
            except Exception:
                raise

    return wrapper


def normalizeDecorator(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "normalize" in kwargs:
            normalize = kwargs.pop("normalize", None)
            try:
                dev = args[0].dev
            except:
                dev = args[0]

            if dev._normalize != normalize:
                restore_transform = dev.transform

                if normalize is False:
                    try:
                        dev.transform = dev._nc_transform
                        result = function(*args, **kwargs)
                        dev.transform = restore_transform
                        return result
                    except Exception:
                        dev.transform = restore_transform
                        raise
                else:
                    try:
                        dev.transform = dev._norm_transform
                        result = function(*args, **kwargs)
                        dev.transform = restore_transform
                        return result
                    except Exception:
                        dev.transform = restore_transform
                        raise
            else:
                try:
                    return function(*args, **kwargs)
                except Exception:
                    raise
        else:
            try:
                return function(*args, **kwargs)
            except Exception:
                raise

    return wrapper


def ignoreWarnDecorator(function):
    """
    Ignore warnings if all <rpc-error> elements are at severity 'warning' and
    match one of the values of the ignore_warning argument.

    For example::
        dev.rpc.get(ignore_warning=True)
        dev.rpc.get(ignore_warning='vrrp subsystem not running')
        dev.rpc.get(ignore_warning=['vrrp subsystem not running',
                                    'statement not found'])
        cu.load(cnf, ignore_warning='statement not found')

    :ignore_warning: A boolean, string or list of string.
        If the value is True, it will ignore all warnings regarldess of the
        warning message. If the value is a string, it will ignore warning(s) if
        the message of each warning matches the string. If the value is a list
        of strings, ignore warning(s) if the message of each warning matches at
        least one of the strings in the list.

    .. note::
            When the value of ignore_warning is a string, or list of strings,
            the string is actually used as a case-insensitive regular
            expression pattern. If the string contains only alpha-numeric
            characters, as shown in the above examples, this results in a
            case-insensitive substring match. However, any regular expression
            pattern supported by the re library may be used for more
            complicated match conditions.
    """

    @wraps(function)
    def wrapper(self, *args, **kwargs):
        ignore_warning = kwargs.pop("ignore_warning", False)
        rsp = None
        try:
            rsp = function(self, *args, **kwargs)
        except RPCError as ex:
            if hasattr(ex, "xml") and ignore_warning:
                if hasattr(ex, "errors"):
                    errors = ex.errors
                else:
                    errors = [ex]
                for err in errors:
                    if err.severity == "warning":
                        if (
                            sys.version < "3"
                            and isinstance(ignore_warning, (str, unicode))
                        ) or (sys.version >= "3" and isinstance(ignore_warning, str)):
                            if not re.search(ignore_warning, err.message, re.I):
                                # Message did not match.
                                raise ex
                        elif isinstance(ignore_warning, list):
                            for warn_msg in ignore_warning:
                                if re.search(warn_msg, err.message, re.I):
                                    # Warning matches.
                                    # Break skips else.
                                    break
                            else:
                                # Message didn't match any of the
                                # ignore_warn pattern values.
                                raise ex
                    else:
                        # Not a warning (probably an error).
                        raise ex
                # Every err was a warning that matched ignore_warning.
                # Prepare the response which will get returned.
                # ex.xml contains the raw xml response which was
                # received, but might be rooted at an <rpc-error> element.
                # Set rsp to the root <rpc-reply> element.
                rsp = ex.xml.getroottree().getroot()
                # 1) A normal response has been run through the XSLT
                #    transformation, but ex.xml has not. Do that now.
                encode = None if sys.version < "3" else "unicode"
                rsp = NCElement(
                    etree.tostring(rsp, encoding=encode), self.transform()
                )._NCElement__doc
                # 2) Now remove all of the <rpc-error> elements from
                #    the response. We've already confirmed they are
                #    all warnings
                rsp = etree.fromstring(str(JXML.strip_rpc_error_transform(rsp)))
            else:
                # ignore_warning was false, or an RPCError which doesn't have
                #  an XML attribute. Raise it up for the caller to deal with.
                raise ex
        return rsp

    return wrapper


def checkSAXParserDecorator(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        # args[0] is self
        use_filter = kwargs.pop("use_filter", args[0]._use_filter)
        restore_value = args[0]._use_filter
        args[0]._use_filter = use_filter
        try:
            if args[0].D != None:
                func = args[0].D.transform
            result = function(*args, **kwargs)
            args[0]._use_filter = restore_value
            if args[0].D != None:
                args[0].D.transform = func
            return result
        except Exception:
            args[0]._use_filter = restore_value
            raise

    return wrapper
