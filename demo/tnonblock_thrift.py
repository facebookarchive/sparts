# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.vservice import VService
from sparts.tasks.thrift import NBServerTask
from sparts.tasks.fb303 import FB303HandlerTask
from sparts.tasks.thrift.handler import ThriftHandlerTask

from sparts.gen.sparts_examples import SpartsFooService, SpartsBarService

class FooServiceHandler(ThriftHandlerTask):
    MODULE = SpartsFooService
    def foo(self):
        return "foo is better!"

FooServiceHandler.register()

class BarServiceHandler(ThriftHandlerTask):
    MODULE = SpartsBarService
    def bar(self):
        return "bar is better!"

BarServiceHandler.register()


NBServerTask.register()
NBServerTask.MULTIPLEX = True

FB303HandlerTask.register()


if __name__ == '__main__':
    VService.initFromCLI()
