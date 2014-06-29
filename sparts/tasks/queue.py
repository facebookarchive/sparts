# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Module for tasks related to doing work from a queue"""
from concurrent.futures import Future
from six.moves import queue
from sparts.counters import counter, samples, SampleType, CallbackCounter
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

    execute_duration_ms = samples(windows=[60, 240],
       types=[SampleType.AVG, SampleType.MAX, SampleType.MIN])
    n_trylater = counter()
    n_completed = counter()
    n_unhandled = counter()

    def execute(self, item, context):
        """Implement this in your QueueTask subclasses"""
        raise NotImplementedError()

    def initTask(self):
        super(QueueTask, self).initTask()
        self.queue = queue.Queue(maxsize=self.max_items)
        self.counters['queue_depth'] = \
            CallbackCounter(lambda: self.queue.qsize())
        self._shutdown_sentinel = object()

    def stop(self):
        super(QueueTask, self).stop()
        self.queue.put(self._shutdown_sentinel)

    def submit(self, item):
        """Enqueue `item` into this task's Queue.  Returns a `Future`"""
        future = Future()
        work = ExecuteContext(item=item, future=future)
        self.queue.put(work)
        return future

    def map(self, items, timeout=None):
        """Enqueues `items` into the queue"""
        futures = map(self.submit, items)
        return [f.result(timeout) for f in futures]

    def _runloop(self):
        while not self.service._stop:
            try:
                item = self.queue.get(timeout=1.0)
                if item is self._shutdown_sentinel:
                    self.queue.put(item)
                    break
            except queue.Empty:
                continue

            # Create an ExecuteContext if we didn't have one
            if isinstance(item, ExecuteContext):
                context = item
                item = context.item
            else:
                context = ExecuteContext(item=item)

            try:
                context.start()
                result = self.execute(item, context)
                self.n_completed.increment()
                self.execute_duration_ms.add(context.elapsed * 1000.0)
                context.set_result(result)
            except TryLater:
                self.n_trylater.increment()
                context.attempt += 1
                self.queue.put(context)
            except Exception as ex:
                self.n_unhandled.increment()
                self.execute_duration_ms.add(context.elapsed * 1000.0)
                handled = context.set_exception(ex)
                if not handled:
                    raise

            finally:
                self.queue.task_done()
