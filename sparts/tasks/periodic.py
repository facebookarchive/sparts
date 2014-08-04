# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from __future__ import absolute_import

from sparts.counters import counter, samples, SampleType
from sparts.sparts import option
from sparts.timer import Timer
from sparts.vtask import VTask, TryLater
from threading import Event


class PeriodicTask(VTask):
    """Task that executes `execute` at a specified interval
    
    You must either override the `INTERVAL` (seconds) class attribute, or
    pass a --{OPT_PREFIX}-interval in order for your task to run.
    """
    INTERVAL = None

    execute_duration_ms = samples(windows=[60, 240],
       types=[SampleType.AVG, SampleType.MAX, SampleType.MIN])
    n_iterations = counter()
    n_slow_iterations = counter()
    n_try_later = counter()

    interval = option(type=float, metavar='SECONDS',
                      default=lambda cls: cls.INTERVAL,
                      help='How often this task should run [%(default)s] (s)')

    def execute(self, context=None):
        """Override this to perform some custom action periodically."""
        self.logger.debug('execute')

    def initTask(self):
        # Register an event that we can more smartly wait on in case shutdown
        # is requested while we would be `sleep()`ing
        self.stop_event = Event()

        super(PeriodicTask, self).initTask()

        assert self.interval is not None, \
            "INTERVAL must be defined on %s or --%s-interval passed" % \
            (self.name, self.name)

    def stop(self):
        self.stop_event.set()
        super(PeriodicTask, self).stop()

    def _runloop(self):
        timer = Timer()
        timer.start()
        while not self.service._stop:
            try:
                self.execute()
            except TryLater:
                self.n_try_later.increment()
                continue

            self.n_iterations.increment()
            self.execute_duration_ms.add(timer.elapsed * 1000)
            to_sleep = self.interval - timer.elapsed
            if to_sleep > 0:
                if self.stop_event.wait(to_sleep):
                    return
            else:
                self.n_slow_iterations.increment()

            timer.start()
