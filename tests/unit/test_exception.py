__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from jnpr.junos.exception import RpcError, CommitError
from lxml import etree

class Test_RpcError(unittest.TestCase):

    def test_rpcerror_repr(self):
        rsp = etree.XML('<root><a>test</a></root>')
        obj = RpcError(rsp = rsp)
        self.assertEquals(str, type(obj.__repr__()))
        self.assertEqual(obj.__repr__(), '<root>\n  <a>test</a>\n</root>\n')

    def test_rpcerror_jxml_check(self):
        #this test is intended to hit jxml code
        rsp = etree.XML('<rpc-reply><a>test</a></rpc-reply>')
        obj = CommitError(rsp = rsp)
        self.assertEqual(type(obj.rpc_error), dict)

