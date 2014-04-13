# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Module that provides helpers for supporting thrift over HTTP in tornado."""
from __future__ import absolute_import

import tornado.web
from thrift.transport.TTransport import TMemoryBuffer
from thrift.protocol.TBinaryProtocol import TBinaryProtocol


class TornadoThriftHandler(tornado.web.RequestHandler):
    """A WebRequest handler that integrates HTTP with a thrift `Processor`.
    
    This handler MUST be initialized with a `processor` kwarg in an
    application config that includes it.
    """

    def initialize(self, processor):
        if hasattr(processor, 'processor'):
            processor = processor.processor
        self.processor = processor

    def post(self):
        """Thrift HTTP POST request.
        
        Translates the POST body to the thrift request, and returns the
        serialized thrift message in the response body.  Sets the approprate
        HTTP Content-Type header as well.
        """
        iprot = TBinaryProtocol(TMemoryBuffer(self.request.body))
        oprot = TBinaryProtocol(TMemoryBuffer())
        self.processor.process(iprot, oprot)
        self.set_header('Content-Type', 'application/x-thrift')
        self.write(oprot.trans.getvalue())
