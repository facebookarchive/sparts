# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Sparts module implementing a basic timer class"""
import time
from datetime import timedelta

class Timer(object):
    """Basic Timer class that can be used as a context manager."""
    def __init__(self):
        self.start_time = self.end_time = None

    def __enter__(self):
        """ContextManager protocol enter to start the timer"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """ContextManager protocol exit to stop the timer"""
        self.stop()

    def start(self):
        """Explicitly start/restart the timer"""
        self.start_time = self._time()

    def stop(self):
        """Explicitly stop the timer"""
        self.end_time = self._time()

    @property
    def elapsed(self):
        """Return the duration that the timer was/is active"""
        # If the timer is not started, return 0.0
        if self.start_time is None:
            return 0.0

        # If the timer has not stopped, return the elapsed time until now
        if self.end_time is None:
            return self._time() - self.start_time

        # If the timer has stopped, return the difference in times
        return self.end_time - self.start_time

    def __str__(self):
        return str(timedelta(seconds=self.elapsed))

    def _time(self):
        """Private-ish time to help with mocking/unittests"""
        return time.time()


def run_until_true(f, timeout):
    """Runs function `f` until it returns True or `timeout` elapses.
    
    Returns if f returns True.  Raises if timeout is exceeded."""
    with Timer() as t:
        while t.elapsed < timeout:
            if f():
                return
            time.sleep(0.001)

    raise Exception("%.1fs Timeout Exceeded waiting for %s to complete" %
                    (timeout, f))
