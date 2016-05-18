# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Verify futures functionality of QueueTasks"""
from sparts.tasks.queue import QueueTask
from sparts.tests.base import SingleTaskTestCase, Skip
from sparts.vtask import ExecuteContext, TryLater

try:
    from concurrent import futures
except ImportError:
    raise Skip("futures must be installed to run this test")


class BarTask(QueueTask):
    """Helper task.  Returns results for callbacks.

    Appends "bar" to input string, "baz" to exception message if
    `do_raise` class attribute is set to True"""
    do_raise = False
    do_trylater = False

    def execute(self, item, context):
        if self.do_trylater:
            raise TryLater(item + ":TryLater")
        if self.do_raise:
            raise Exception(item + 'baz')

        return item + 'bar'


class FutureTests(SingleTaskTestCase):
    TASK = BarTask

    def makeContext(self, item):
        """Helper for making an ExecuteContext with a default future"""
        return ExecuteContext(item=item, future=futures.Future())

    def test_future_wait(self):
        """Make sure waiting for results works"""
        # Put a piece of work in the queue
        ctx = self.makeContext('foo')
        self.task.queue.put(ctx)

        # Wait for it to complete, check the result
        result = ctx.future.result(5.0)
        self.assertEqual(result, 'foobar')

        # Put a piece of work in the queue with the put API
        self.submit('ham')
        future = self.submit('spam')
        self.submit('eggs')
        result = future.result(5.0)
        self.assertEqual(result, 'spambar')

    def submit(self, item):
        return self.task.submit(item)

    def map(self, items, timeout=None):
        return self.task.map(items, timeout=timeout)

    def test_map(self):
        """Test out the futures-based map API"""
        inputs = map(str, range(5))
        results = self.map(inputs)
        self.assertEqual(results, ['0bar', '1bar', '2bar', '3bar', '4bar'])

    def test_map_timeout(self):
        """Test out the futures-based map API"""
        self.task.do_trylater = True

        inputs = map(str, range(5))
        with self.assertRaises(futures.TimeoutError):
            self.map(inputs, timeout=0.05)

    def test_future_raise(self):
        """Make sure raising exceptions works properly.
        
        .result() should raise and .exception() should return the unhandled
        exception"""
        # Make all tasks raise
        self.task.do_raise = True

        # Put a piece of work in the queue
        ctx = self.makeContext('foo')
        self.task.queue.put(ctx)

        # Result should raise, since there was an unhandled exception
        with self.assertRaises(Exception) as cm:
            ctx.future.result(5.0)

        # Make sure these are the right exceptions
        self.assertEqual(str(cm.exception), 'foobaz')
        self.assertEqual(str(ctx.future.exception(5.0)), 'foobaz')

    def test_future_trylater(self):
        """Make sure starting the work marks the future as running"""
        # Force all work to TryLater instead of complete
        self.task.do_trylater = True

        # Put work in the queue
        ctx = self.makeContext('foo')
        self.task.queue.put(ctx)
        self.task.queue.put('another')

        # Wait for the first execution to start
        ctx.running.wait()

        # Future should be marked running
        self.assertTrue(ctx.future.running())

        # queue_depth counter should return > 0 as well
        self.assertGreater(self.task.getCounter('queue_depth')(), 0)
        self.assertGreater(self.service.getCounters()['BarTask.queue_depth'](), 0)
        self.assertGreater(self.service.getCounter('BarTask.queue_depth')(), 0)

        # Now make sure that calling result() will timeout (since we are in
        # a tight TryLater loop)
        with self.assertRaises(futures.TimeoutError):
            ctx.future.result(0.0)

        # Disable TryLater
        self.task.do_trylater = False

        # Wait for it to complete, check the result
        result = ctx.future.result(5.0)
        self.assertEqual(result, 'foobar')

    def test_future_runloop_raises(self):
        """Unhandled exception does not kill the whole loop."""
        self.task.do_raise = True

        fut = self.task.submit('not-an-actual-task')

        # This should not raise an exception even if - wait for the main thread
        # for half a second
        self.runloop.join(0.5)

        # The main thread should still be alive...
        self.assertTrue(self.runloop.isAlive())

        # The future should have an exception set on it
        self.assertTrue(fut.exception())
