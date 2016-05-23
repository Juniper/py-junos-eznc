import re
import time
from jnpr.junos.netconify import cmdo
from lxml import etree
from lxml.builder import E
from datetime import datetime, timedelta


from jnpr.junos.netconify.fact import Fact

__all__ = ['xmlmode_netconf']

_NETCONF_EOM = ']]>]]>'
_xmlns = re.compile('xmlns=[^>]+')
_xmlns_strip = lambda text: _xmlns.sub('', text)
_junosns = re.compile('junos:')
_junosns_strip = lambda text: _junosns.sub('', text)

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
        self.facts = Fact(self)

    # -------------------------------------------------------------------------
    # NETCONF session open and close
    # -------------------------------------------------------------------------

    def open(self, at_shell):
        """ start the XML API process and receive the 'hello' message """
        nc_cmd = ('junoscript', 'xml-mode')[at_shell]
        self._tty.write(nc_cmd + ' netconf need-trailer')
        mark_start = datetime.now()
        mark_end = mark_start + timedelta(seconds=15)
        #pdb.set_trace()

        while datetime.now() < mark_end:
            time.sleep(0.1)
            line = self._tty.read()
            if cmdo.verbose == 2:
                print(line)  #enable to see received NETCONF xml
            if line.startswith("<!--"):
                break
        else:
            # exceeded the while loop timeout
            raise RuntimeError("Netconify Error: netconf not responding")

        self.hello = self._receive()

    """
    def open(self, at_shell):
        # start the XML API process and receive the 'hello' message 

        nc_cmd = ('junoscript', 'xml-mode')[at_shell]
        self._tty.write(nc_cmd + ' netconf need-trailer')

        while True:
            time.sleep(0.1)
            line = self._tty.read()
            if line.startswith("<!--"):
                break

        self.hello = self._receive()
    """

    def close(self, force=False):
        """ issue the XML API to close the session """

        # if we do not have an open connection, then return now.
        if force is False:
            if self.hello is None:
                return

        self.rpc('close-session')
        # removed flush

    # -------------------------------------------------------------------------
    # Junos OS configuration methods
    # -------------------------------------------------------------------------

    def load(self, content, **kvargs):
        """
        load-override a Junos 'conf'-style file into the device.  if the
        load is successful, return :True:, otherwise return the XML reply
        structure for further processing
        """
        action = kvargs.get('action', 'override')
        cmd = E('load-configuration', dict(format='text', action=action),
                E('configuration-text', content)
                )
        rsp = self.rpc(etree.tostring(cmd))
        return rsp if rsp.findtext('.//ok') is None else True

    def commit_check(self):
        """
        performs the Junos 'commit check' operation.  if successful return
        :True: otherwise return the response as XML for further processing.
        """
        rsp = self.rpc('<commit-configuration><check/></commit-configuration>')
        return True if 'ok' == rsp.tag else rsp

    def commit(self):
        """
        performs the Junos 'commit' operation.  if successful return
        :True: otherwise return the response as XML for further processing.
        """
        rsp = self.rpc('<commit-configuration/>')
        if 'ok' == rsp.tag:
            return True     # some devices use 'ok'
        if len(rsp.xpath('.//commit-success')) > 0:
            return True
        return rsp

    def rollback(self):
        """ rollback that recent changes """
        cmd = E('load-configuration', dict(compare='rollback', rollback="0"))
        return self.rpc(etree.tostring(cmd))

    # -------------------------------------------------------------------------
    # MISC device commands
    # -------------------------------------------------------------------------

    def reboot(self, in_min=0):
        """ issue a reboot to the device """
        cmd = E('request-reboot', E('in', str(in_min)))
        rsp = self.rpc(etree.tostring(cmd))
        return True

    def poweroff(self, in_min=0):
        """ issue a reboot to the device """
        cmd = E('request-power-off', E('in', str(in_min)))
        rsp = self.rpc(etree.tostring(cmd))
        return True

    def zeroize(self):
        """ issue a reboot to the device """
        cmd = E.command('request system zeroize')
        try:
            rsp = self.rpc(etree.tostring(cmd))
        except:
            pass
        return True

    def enablecluster(self, cluster_id, node):
        """ issue request chassis cluster command """
        cmd = E('set-chassis-cluster-enable',
                E('cluster-id',
                  str(cluster_id)),
                E('node',
                  str(node)),
                E('reboot'))
        rsp = self.rpc(etree.tostring(cmd))
        # device will be set to new cluster ID:NODE value
        return True

    def disablecluster(self):
        """ issue set chassis cluster disable to the device nad reboot """
        cmd = E.command('set chassis cluster disable reboot')
        rsp = self.rpc(etree.tostring(cmd))
        # No need to check error exception, device will be rebooted even if not
        # in cluster
        return True

    def enablecluster(self, cluster_id, node):
        """ issue request chassis cluster command """
        cmd = E('set-chassis-cluster-enable',
                E('cluster-id',
                  str(cluster_id)),
                E('node',
                  str(node)),
                E('reboot'))
        rsp = self.rpc(etree.tostring(cmd))
        # device will be set to new cluster ID:NODE value
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
        self._tty.rawwrite('<rpc>{0}</rpc>'.format(cmd))
        rsp = self._receive()
        try:
            return rsp[0]  # return first child after the <rpc-reply>
        except:
            return etree.XML('<error-in-receive/>')

    # -------------------------------------------------------------------------
    # LOW-LEVEL I/O for reading back XML response
    # -------------------------------------------------------------------------

    def _receive(self):
        """ process the XML response into an XML object """
        rxbuf = []
        mark_start = datetime.now()
        mark_end = mark_start + timedelta(seconds=30)
        while datetime.now() < mark_end:
            time.sleep(0.1)
            line = self._tty.read().strip().replace('\x07','')
            if cmdo.verbose == 2:
                print(line)  # enable to see received xml messages
            if not line:
                continue  # if we got nothin, go again
            if _NETCONF_EOM == line:
                break  # check for end-of-message
            rxbuf.append(line)

        rxbuf[0] = _xmlns_strip(rxbuf[0])  # nuke the xmlns
        rxbuf[1] = _xmlns_strip(rxbuf[1])  # nuke the xmlns
        rxbuf = map(_junosns_strip, rxbuf)  # nuke junos: namespace
        try:
            as_xml = etree.XML(''.join(rxbuf))
            return as_xml
        except:
            if '</xnm:error>' in rxbuf:
                for x in rxbuf:
                    if '<message>' in x:
                        return etree.XML(
                            '<error-in-receive>' + x + '</error-in-receive>')
            else:
                return etree.XML('<error-in-receive/>')
