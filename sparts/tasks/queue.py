# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Module for tasks related to doing work from a queue"""
from concurrent.futures import Future
from six.moves import queue
from sparts.collections import PriorityQueue, UniqueQueue
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

    def _makeQueue(self):
        """Override this if you need a custom Queue implementation"""
        return queue.Queue(maxsize=self.max_items)

    def initTask(self):
        super(QueueTask, self).initTask()
        self.queue = self._makeQueue()
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
                context.raw_wrapped = False
            else:
                context = ExecuteContext(item=item)
                context.raw_wrapped = True

            try:
                context.start()
                result = self.execute(item, context)
                self.work_success(context, result)
            except TryLater:
                self.work_retry(context)
            except Exception as ex:
                self.work_fail(context, ex)

            finally:
                self.queue.task_done()

    def work_success(self, context, result):
        self.n_completed.increment()
        self.execute_duration_ms.add(context.elapsed * 1000.0)
        context.set_result(result)
        self.work_done(context)

    def work_retry(self, context):
        self.n_trylater.increment()
        context.attempt += 1
        self.work_done(context)
        self.queue.put(context)

    def work_fail(self, context, exception):
        self.n_unhandled.increment()
        self.execute_duration_ms.add(context.elapsed * 1000.0)
        handled = context.set_exception(exception)
        self.work_done(context)
        if not handled:
            raise

    def work_done(self, context):
        pass

class PriorityQueueTask(QueueTask):
    # TODO: There is a possible shutdown crash in python-3, when there is
    # outstanding work in the queue, but the sentinel object is inserted:
    # the sentinal object isn't generally of a comparable type.
    def _makeQueue(self):
        return PriorityQueue(maxsize=self.max_items)


class UniqueQueueTask(QueueTask):
    def _makeQueue(self):
        q = UniqueQueue(maxsize=self.max_items)
        q.explicit_unsee = True
        return q

    def work_done(self, context):
        super(UniqueQueueTask, self).work_done(context)
        if context.raw_wrapped:
            self.queue.unsee(context.item)
        else:
            self.queue.unsee(context)
