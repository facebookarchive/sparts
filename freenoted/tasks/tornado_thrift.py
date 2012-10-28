from __future__ import absolute_import

import tornado.web
from thrift.transport.TTransport import TMemoryBuffer
from thrift.protocol.TBinaryProtocol import TBinaryProtocol


class TornadoThriftHandler(tornado.web.RequestHandler):
    def initialize(self, processor):
        self.processor = processor
    
    def post(self):
        iprot = TBinaryProtocol(TMemoryBuffer(self.request.body))
        oprot = TBinaryProtocol(TMemoryBuffer())
        self.processor.process(iprot, oprot)
        self.set_header('Content-Type', 'application/x-thrift')
        self.write(oprot.trans.getvalue())
