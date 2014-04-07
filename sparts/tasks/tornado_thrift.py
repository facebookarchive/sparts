# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from __future__ import absolute_import

import tornado.web
from thrift.transport.TTransport import TMemoryBuffer
from thrift.protocol.TBinaryProtocol import TBinaryProtocol


class TornadoThriftHandler(tornado.web.RequestHandler):
    def initialize(self, processor):
        if hasattr(processor, 'processor'):
            processor = processor.processor
        self.processor = processor

    def post(self):
        iprot = TBinaryProtocol(TMemoryBuffer(self.request.body))
        oprot = TBinaryProtocol(TMemoryBuffer())
        self.processor.process(iprot, oprot)
        self.set_header('Content-Type', 'application/x-thrift')
        self.write(oprot.trans.getvalue())
