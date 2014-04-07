# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tasks.periodic import PeriodicTask
from ..base import SingleTaskTestCase
import time
import threading


class MyTask(PeriodicTask):
    INTERVAL = 0.1
    counter = 0

    def initTask(self):
        super(MyTask, self).initTask()
        self.visit_threads = set()

    def execute(self):
        self.counter += 1
        self.visit_threads.add(threading.current_thread().ident)

class TestMyTask(SingleTaskTestCase):
    TASK = MyTask

    def test_execute_happens(self):
        t0 = time.time()
        while self.task.counter <= 0 and time.time() - t0 < 3.0:
            time.sleep(0.101)
        self.assertGreater(self.task.counter, 0)


class MyMultiTask(MyTask):
    workers = 5

class TestMultiTask(SingleTaskTestCase):
    TASK = MyMultiTask
    def test_multi_execute(self):
        t0 = time.time()
        while len(self.task.visit_threads) < 5 and time.time() - t0 < 3.0:
            time.sleep(0.101)
        self.assertGreaterEqual(self.task.counter, 5)
