# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tasks.periodic import PeriodicTask
from sparts.tests.base import SingleTaskTestCase
from sparts.timer import Timer
import time
import threading


class MyTask(PeriodicTask):
    INTERVAL = 0.1
    counter = 0
    fail_async = False

    def initTask(self):
        super(MyTask, self).initTask()
        self.visit_threads = set()

    def execute(self):
        if self.fail_async and self.has_pending():
            raise Exception("fail_async")

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
        f = self.task.execute_async()
        with self.assertRaises(Exception) as ctx:
            f.result()
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


class MyMultiTask(MyTask):
    workers = 5

class TestMultiTask(SingleTaskTestCase):
    TASK = MyMultiTask
    def test_multi_execute(self):
        with Timer() as t:
            while len(self.task.visit_threads) < 5 and t.elapsed < 3.0:
                time.sleep(0.101)
        self.assertGreaterEqual(self.task.counter, 5)
