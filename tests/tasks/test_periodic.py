# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tasks.periodic import PeriodicTask
from sparts.tests.base import SingleTaskTestCase
from sparts.timer import Timer
from sparts.vtask import TryLater

import time
import threading


class MyTask(PeriodicTask):
    INTERVAL = 0.05
    counter = 0
    fail_async = False
    trylater = False

    def initTask(self):
        super(MyTask, self).initTask()
        self.visit_threads = set()

    def execute(self):
        if self.fail_async and self.has_pending():
            raise Exception("fail_async")
        if self.trylater:
            raise TryLater(str(self.trylater), after=self.trylater)

        self.logger.debug("%s: Execute OK", time.time())
        self.counter += 1
        self.visit_threads.add(threading.current_thread().ident)
        return self.counter


class TestMyTask(SingleTaskTestCase):
    TASK = MyTask

    def test_execute_happens(self):
        with Timer() as t:
            while self.task.counter <= 0 and t.elapsed < 3.0:
                time.sleep(0.101)
        self.assertGreater(self.task.counter, 0)

    def test_execute_async(self):
        f = self.task.execute_async()
        res = f.result(3.0)
        self.assertNotNone(res)
        self.assertGreater(res, 0)

        # Verify exception path
        self.task.fail_async = True
        with self.assertRaises(Exception) as ctx:
            # Call this twice, since there's a race condition where setting
            # fail_async and getting the future from execute_async is called
            # when execute is between the self.fail_async check and the return
            self.task.execute_async().result(1.0)
            self.task.execute_async().result(1.0)

        self.assertEqual(ctx.exception.args[0], "fail_async")

        # Wait until task shuts down
        with Timer() as t:
            while t.elapsed < 5.0:
                if not self.task.running:
                    break
            self.assertFalse(self.task.running)

        # Verify early exception on async_execute against shutdown tasks
        f = self.task.execute_async()
        with self.assertRaises(Exception) as ctx:
            f.result()
        self.assertEqual(ctx.exception.args[0], "Worker not running")

    def test_trylater_after(self):
        t = self.task
        # Set up some mocks
        t._handle_try_later = self.mock.Mock(wraps=t._handle_try_later)
        t.stop_event = self.mock.Mock(wraps=t.stop_event)

        # Run once with no TryLater
        t.execute_async().result()
        self.assertFalse(t._handle_try_later.called)

        # Run once with no TryLater
        t.trylater = 0.01

        # Wait for it to get called once
        t0 = time.time()
        while not t._handle_try_later.called and time.time() - t0 < 5.0:
            time.sleep(0.01)
        self.assertTrue(t._handle_try_later)

        # Disable trylater and wait for one successful completion
        t.trylater = None
        t.execute_async().result(5.0)

        # Make sure things were called with good values
        self.assertTrue(t._handle_try_later)
        self.task.stop_event.wait.assert_any_call(0.01)

class MyMultiTask(MyTask):
    workers = 5

class TestMultiTask(SingleTaskTestCase):
    TASK = MyMultiTask
    def test_multi_execute(self):
        with Timer() as t:
            while len(self.task.visit_threads) < 5 and t.elapsed < 3.0:
                time.sleep(0.101)
        self.assertGreaterEqual(self.task.counter, 5)
