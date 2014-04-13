# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from ..vtask import VTask, TryLater
import time
from ..sparts import option, counter, samples, SampleType
from threading import Event


class PeriodicTask(VTask):
    INTERVAL = None

    execute_duration_ms = samples(windows=[60, 240],
       types=[SampleType.AVG, SampleType.MAX, SampleType.MIN])
    n_iterations = counter()
    n_slow_iterations = counter()
    n_try_later = counter()

    interval = option(type=float, metavar='SECONDS',
                      default=lambda cls: cls.INTERVAL,
                      help='How often this task should run [%(default)s] (s)')

    def initTask(self):
        super(PeriodicTask, self).initTask()
        assert self.interval is not None
        self.stop_event = Event()

    def stop(self):
        self.stop_event.set()
        super(PeriodicTask, self).stop()

    def _runloop(self):
        t0 = time.time()
        while not self.service._stop:
            try:
                self.execute()
            except TryLater:
                self.n_try_later.increment()
                continue

            self.n_iterations.increment()
            self.execute_duration_ms.add((time.time() - t0) * 1000)
            to_sleep = (t0 + self.interval) - time.time()
            if to_sleep > 0:
                if self.stop_event.wait(to_sleep):
                    return
            else:
                self.n_slow_iterations.increment()

            t0 = time.time()

    def execute(self, context=None):
        self.logger.debug('execute')
