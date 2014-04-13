# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Module for tasks related to doing work from a queue"""
from six.moves import queue
from sparts.sparts import option
from sparts.vtask import VTask, ExecuteContext, TryLater

class QueueTask(VTask):
    """Task that calls `execute` for all work put on its `queue`"""
    MAX_ITEMS = 0
    WORKERS = 1
    max_items = option(type=int, default=lambda cls: cls.MAX_ITEMS,
                       help='Set a bounded queue length.  This may '
                            'cause unexpected deadlocks. [%(default)s]')
    workers = option(type=int, default=lambda cls: cls.WORKERS,
                     help='Number of threads to spawn to work on items from '
                          'its queue. [%(default)s]')

    def execute(self, item, context):
        """Implement this in your QueueTask subclasses"""
        raise NotImplementedError()

    def initTask(self):
        super(QueueTask, self).initTask()
        self.queue = queue.Queue(maxsize=self.max_items)
        self._shutdown_sentinel = object()

    def stop(self):
        super(QueueTask, self).stop()
        self.queue.put(self._shutdown_sentinel)

    def _runloop(self):
        while not self.service._stop:
            try:
                item = self.queue.get(timeout=1.0)
                if item is self._shutdown_sentinel:
                    self.queue.put(item)
                    break
            except queue.Empty:
                continue

            if isinstance(item, ExecuteContext):
                context = item
                item = context.item
            else:
                context = ExecuteContext(item=item)
            try:
                result = self.execute(item, context)
                if context.deferred is not None:
                    context.deferred.callback(result)
            except TryLater:
                context.attempt += 1
                self.queue.put(context)
            except Exception as ex:
                if context.deferred is not None:
                    self.unhandled = None
                    context.deferred.addErrback(self.unhandledErrback)
                    context.deferred.errback(ex)
                    if self.unhandled is not None:
                        self.unhandled.raiseException()
                else:
                    raise
            finally:
                self.queue.task_done()

    def unhandledErrback(self, error):
        self.unhandled = error
        return None
