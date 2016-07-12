import re
import time
from lxml import etree
import select
import socket
import logging

from lxml.builder import E
from datetime import datetime, timedelta
from jnpr.junos.jxml import remove_namespaces
from jnpr.junos import exception as EzErrors
import six


class PY6:
    NEW_LINE = six.b('\n')
    EMPTY_STR = six.b('')
    NETCONF_EOM = six.b(']]>]]>')
    STARTS_WITH = six.b("<!--")

__all__ = ['xmlmode_netconf']

_NETCONF_EOM = six.b(']]>]]>')
_xmlns = re.compile(six.b('xmlns=[^>]+'))
_xmlns_strip = lambda text: _xmlns.sub(PY6.EMPTY_STR, text)
_junosns = re.compile(six.b('junos:'))
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

    # -------------------------------------------------------------------------
    # NETCONF session open and close
    # -------------------------------------------------------------------------

    def open(self, at_shell):
        """ start the XML API process and receive the 'hello' message """
        nc_cmd = ('junoscript', 'xml-mode')[at_shell]
        self._tty.write(nc_cmd + ' netconf need-trailer')
        mark_start = datetime.now()
        mark_end = mark_start + timedelta(seconds=15)

        while datetime.now() < mark_end:
            time.sleep(0.1)
            line = self._tty.read()
            if line.startswith(PY6.STARTS_WITH):
                break
        else:
            # exceeded the while loop timeout
            raise RuntimeError("Netconify Error: netconf not responding")

        self.hello = self._receive()

    def close(self, force=False):
        """ issue the XML API to close the session """

        # if we do not have an open connection, then return now.
        if force is False:
            if self.hello is None:
                return

        self.rpc('close-session')
        # removed flush

    # -------------------------------------------------------------------------
    # MISC device commands
    # -------------------------------------------------------------------------

    def zeroize(self):
        """ issue a reboot to the device """
        cmd = E.command('request system zeroize')
        try:
            rsp = self.rpc(etree.tounicode(cmd))
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
        if not cmd.startswith('<'):
            cmd = '<{0}/>'.format(cmd)
        rpc = six.b('<rpc>{0}</rpc>'.format(cmd))
        logger.info('Calling rpc: %s' % rpc)
        self._tty.rawwrite(rpc)

        rsp = self._receive()
        try:
            rsp = remove_namespaces(rsp[0])  # return first child after the <rpc-reply>
        except IndexError:
            if rsp.text.strip() is not '':
                return rsp
            # no children, so assume it means we are OK
            return True
        except:
            return etree.XML('<error-in-receive/>')
        err_msg = rsp.findtext('error-message')
        if err_msg:
            if err_msg == 'permission denied':
                e = EzErrors.PermissionError
            else:
                e = EzErrors.RpcError
            raise e(cmd=cmd, rsp=rsp)
        return rsp


    # -------------------------------------------------------------------------
    # LOW-LEVEL I/O for reading back XML response
    # -------------------------------------------------------------------------

    def _receive(self):
        """ process the XML response into an XML object """
        rxbuf = PY6.EMPTY_STR
        lastline = PY6.EMPTY_STR
        line = PY6.EMPTY_STR
        while True:
            line = self._tty.read()
            if not line:
                continue
            if _NETCONF_EOM in line:
                rxbuf = rxbuf+line
                break
            else:
                rxbuf = rxbuf+line
                if _NETCONF_EOM in lastline+line:
                    break
        lastline = line
        rxbuf = rxbuf.splitlines()
        if _NETCONF_EOM in rxbuf[-1]:
            rxbuf.pop()

        rxbuf[0] = _xmlns_strip(rxbuf[0])  # nuke the xmlns
        rxbuf[1] = _xmlns_strip(rxbuf[1])  # nuke the xmlns
        rxbuf = list(map(_junosns_strip, rxbuf))  # nuke junos: namespace
        try:
            rxbuf = [i.strip() for i in rxbuf if i.strip() != PY6.EMPTY_STR]
            rcvd_data = PY6.NEW_LINE.join(rxbuf)
            logger.debug('Received: \n%s' % rcvd_data)
            as_xml = etree.XML(rcvd_data)
            return as_xml
        except:
            if '</xnm:error>' in rxbuf:
                for x in rxbuf:
                    if '<message>' in x:
                        return etree.XML(
                            '<error-in-receive>' + x + '</error-in-receive>')
            else:
                return etree.XML('<error-in-receive/>')

