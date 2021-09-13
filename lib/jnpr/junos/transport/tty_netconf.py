import re
import time
from lxml import etree
import select
import socket
import logging
import sys

from lxml.builder import E
from lxml.etree import XMLSyntaxError
from datetime import datetime, timedelta
from ncclient.operations.rpc import RPCReply, RPCError
from ncclient.xml_ import to_ele
import six
from ncclient.transport.session import HelloHandler


class PY6:
    NEW_LINE = six.b("\n")
    EMPTY_STR = six.b("")
    NETCONF_EOM = six.b("]]>]]>")
    STARTS_WITH = six.b("<!--")


__all__ = ["xmlmode_netconf"]

_NETCONF_EOM = six.b("]]>]]>")
_xmlns = re.compile(six.b("xmlns=[^>]+"))
_xmlns_strip = lambda text: _xmlns.sub(PY6.EMPTY_STR, text)
_junosns = re.compile(six.b("junos:"))
_junosns_strip = lambda text: _junosns.sub(PY6.EMPTY_STR, text)

logger = logging.getLogger("jnpr.junos.tty_netconf")

# =========================================================================
# xmlmode_netconf
# =========================================================================


class tty_netconf(object):

    """
    Basic Junos XML API for bootstraping through the TTY
    """

    def __init__(self, tty):
        self._tty = tty
        self.hello = None
        self._session_id = -1

    # -------------------------------------------------------------------------
    # NETCONF session open and close
    # -------------------------------------------------------------------------

    def open(self, at_shell):
        """start the XML API process and receive the 'hello' message"""
        nc_cmd = ("junoscript", "xml-mode")[at_shell]
        self._tty.write(nc_cmd + " netconf need-trailer")
        mark_start = datetime.now()
        mark_end = mark_start + timedelta(seconds=15)

        while datetime.now() < mark_end:
            time.sleep(0.1)
            line = self._tty.read()
            if line.startswith(PY6.STARTS_WITH):
                break
        else:
            # exceeded the while loop timeout
            raise RuntimeError("Error: netconf not responding")

        self.hello = self._receive()
        self._session_id, _ = HelloHandler.parse(self.hello.decode("utf-8"))

    def close(self, force=False):
        """issue the XML API to close the session"""

        # if we do not have an open connection, then return now.
        if force is False:
            if self.hello is None:
                return

        self.rpc("close-session")
        # removed flush

    # -------------------------------------------------------------------------
    # MISC device commands
    # -------------------------------------------------------------------------

    def zeroize(self):
        """issue a reboot to the device"""
        cmd = E.command("request system zeroize")
        try:
            encode = None if sys.version < "3" else "unicode"
            self.rpc(etree.tostring(cmd, encoding=encode))
        except:
            return False
        return True

    # -------------------------------------------------------------------------
    # XML RPC command execution
    # -------------------------------------------------------------------------

    def rpc(self, cmd):
        """
        Write the XML cmd and return the response as XML object.

        :cmd:
          <str> of the XML command.  if the :cmd: is not XML, then
          this routine will perform the brackets; i.e. if given
          'get-software-information', this routine will turn
          it into '<get-software-information/>'

        NOTES:
          The return XML object is the first child element after
          the <rpc-reply>.  There is also no error-checking
          performing by this routine.
        """
        if not cmd.startswith("<"):
            cmd = "<{}/>".format(cmd)
        rpc = six.b("<rpc>{}</rpc>".format(cmd))
        logger.info("Calling rpc: %s" % rpc)
        self._tty.rawwrite(rpc)

        rsp = self._receive()
        rsp = rsp.decode("utf-8") if isinstance(rsp, bytes) else rsp
        reply = RPCReply(rsp, huge_tree=self._tty._huge_tree)
        errors = reply.errors
        if len(errors) > 1:
            raise RPCError(to_ele(reply._raw), errs=errors)
        elif len(errors) == 1:
            raise reply.error
        return rsp

    # -------------------------------------------------------------------------
    # LOW-LEVEL I/O for reading back XML response
    # -------------------------------------------------------------------------

    def _receive(self):
        # On windows select.select throws io.UnsupportedOperation: fileno
        # so use read function for windows serial COM ports
        if hasattr(self._tty, "port") and str(self._tty.port).startswith("COM"):
            return self._receive_serial_win()
        else:
            return self._receive_serial()

    def _receive_serial(self):
        """process the XML response into an XML object"""
        rxbuf = PY6.EMPTY_STR
        line = PY6.EMPTY_STR
        while True:
            try:
                rd, wt, err = select.select([self._tty._rx], [], [], 0.1)
            except select.error as err:
                raise err
            except socket.error as err:
                raise err
            if rd:
                line, lastline = rd[0].read_until(PY6.NETCONF_EOM, 0.1), line
                if not line:
                    continue
                if _NETCONF_EOM in line or _NETCONF_EOM in lastline + line:
                    rxbuf = rxbuf + line
                    break
                else:
                    rxbuf = rxbuf + line
                    if _NETCONF_EOM in rxbuf:
                        break
        return self._parse_buffer(rxbuf)

    # -------------------------------------------------------------------------
    # Read message from windows COM ports
    # -------------------------------------------------------------------------

    def _receive_serial_win(self):
        """process incoming data from windows port"""
        rxbuf = PY6.EMPTY_STR
        line = PY6.EMPTY_STR
        while True:
            line, lastline = self._tty.read().strip(), line
            if not line:
                continue
            if _NETCONF_EOM in line or _NETCONF_EOM in lastline + line:
                rxbuf = rxbuf + line
                break
            else:
                rxbuf = rxbuf + line
                if _NETCONF_EOM in rxbuf:
                    break
        return self._parse_buffer(rxbuf)

    def _parse_buffer(self, rxbuf):
        rxbuf = rxbuf.splitlines()
        if _NETCONF_EOM in rxbuf[-1]:
            if rxbuf[-1] == _NETCONF_EOM:
                rxbuf.pop()
            else:
                rxbuf[-1] = rxbuf[-1].split(_NETCONF_EOM)[0]
        try:
            rxbuf = [i.strip() for i in rxbuf if i.strip() != PY6.EMPTY_STR]
            rcvd_data = PY6.NEW_LINE.join(rxbuf)
            logger.debug("Received: \n%s" % rcvd_data)
            parser = etree.XMLParser(
                remove_blank_text=True, huge_tree=self._tty._huge_tree
            )
            try:
                etree.XML(rcvd_data, parser)
            except XMLSyntaxError:
                if _NETCONF_EOM in rcvd_data:
                    rcvd_data = rcvd_data[: rcvd_data.index(_NETCONF_EOM)]
                    etree.XML(rcvd_data)  # just to recheck
                else:
                    parser = etree.XMLParser(recover=True)
                    rcvd_data = etree.tostring(etree.XML(rcvd_data, parser=parser))
            return rcvd_data
        except:
            if "</xnm:error>" in rxbuf:
                for x in rxbuf:
                    if "<message>" in x:
                        return etree.XML(
                            "<error-in-receive>" + x + "</error-in-receive>"
                        )
            else:
                return etree.XML("<error-in-receive/>")
