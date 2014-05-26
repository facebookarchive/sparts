# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Module for implementing time-series counters."""
from __future__ import absolute_import

from collections import deque
from functools import partial
from six import next
from sparts.sparts import _Nameable, _Bindable, ProvidesCounters

import time


class SampleType:
    """Pass an array of these in the `types` paremeter to `sample()`"""
    COUNT = 'count'
    SUM = 'sum'
    AVG = 'avg'
    AVERAGE = 'avg'
    MAX = 'max'
    MIN = 'min'


class _BaseCounter(_Nameable, _Bindable, ProvidesCounters):
    """Base type for counter-like things"""
    suffix = 'UNDEF'

    def __init__(self, name=None):
        super(_BaseCounter, self).__init__(name)
        self._initialize()

    def _bind(self, obj):
        return self.__class__(name=self.name)

    def _initialize(self):
        raise NotImplementedError()

    def _genCounterCallbacks(self):
        """Return this counter's (name, value)"""
        yield self.name, self

    def getvalue(self):
        raise NotImplementedError()

    def add(self, value):
        raise NotImplementedError()

    def __call__(self):
        return self.getvalue()

    def __int__(self):
        return int(self.getvalue())

    def __float__(self):
        return float(self.getvalue())

    def __str__(self):
        v = self.getvalue()
        if v is None:
            return '__None__'
        return str(v)


class ValueCounter(_BaseCounter):
    """Base type for counter-like things that have a `._value`"""
    DEFAULT_VALUE = 0.0
    def _initialize(self, value=None):
        self._value = value or self.DEFAULT_VALUE

    def getvalue(self):
        return self._value


class CallbackCounter(_BaseCounter):
    def __init__(self, callback, name=None):
        super(CallbackCounter, self).__init__(name=name)
        self._callback = callback

    def _initialize(self):
        pass

    def getvalue(self):
        return self._callback()


class Sum(ValueCounter):
    """A running total"""
    suffix = SampleType.SUM

    def add(self, value):
        self._value += value

    def increment(self):
        self.add(1.0)

    def incrementBy(self, value):
        self.add(value)

    def reset(self, value=0):
        self._value = value

counter = Sum

class Count(ValueCounter):
    """A running count"""
    suffix = SampleType.COUNT
    DEFAULT_VALUE = 0

    def add(self, value):
        self._value += 1

class Average(_BaseCounter):
    """A running average"""
    suffix = SampleType.AVERAGE

    def _initialize(self):
        self._total = 0.0
        self._count = 0

    def add(self, value):
        # TODO: Re-use sibling total/count counters if present
        # not sure how to do this sensibly
        self._total += value
        self._count += 1

    def getvalue(self):
        if self._count == 0:
            return None
        return self._total / self._count


class Max(ValueCounter):
    """A running maximum"""
    suffix = SampleType.MAX
    DEFAULT_VALUE = None

    def add(self, value):
        if self._value is None:
            self._value = value
        elif value > self._value:
            self._value = value


class Min(ValueCounter):
    """A running minimum"""
    suffix = SampleType.MIN
    DEFAULT_VALUE = None

    def add(self, value):
        if self._value is None:
            self._value = value
        elif value < self._value:
            self._value = value

    def getvalue(self):
        return self._value

# TODO: Percentiles!!


# Lookup for mapping SampleTypes to their respective classes
_SampleMethod = {
    SampleType.COUNT: Count,
    SampleType.SUM: Sum,
    SampleType.AVERAGE: Average,
    SampleType.MAX: Max,
    SampleType.MIN: Min,
}


class Samples(_Nameable, _Bindable, ProvidesCounters):
    """`samples` are used to generate series of counters dynamically

    This is so you can say, keep track of the average duration of some event for
    the last minute, hour, day, etc, and export these as 4 separate counters.
    """
    def __init__(self, types=None, windows=None, name=None):
        super(Samples, self).__init__(name)
        self.types = types or [SampleType.AVERAGE]
        # minutely, hourly
        self.windows = sorted(windows or [60, 3600])
        self.max_window = max(self.windows)
        self.samples = deque()
        self.dirty = True
        self._prev_counters = {}
        self._prev_time = None

    def _bind(self, obj):
        return self.__class__(types=self.types, windows=self.windows,
                              name=self.name)

    def _genCounterCallbacks(self):
        """Yield all the child counters."""
        for subcounter in self.iterkeys():
            yield subcounter, partial(self.getCounter, subcounter)

    def _now(self):
        """Defined to allow unittest overriding"""
        return time.time()

    def add(self, value):
        now = self._now()
        self.samples.append((now, value))

        # When adding samples, trim old ones.
        while now - self.max_window > self.samples[0][0]:
            self.samples.popleft()
        self.dirty = True

        # TODO: Handle "infinite" windows

    def getCounters(self):
        if self.dirty is False and self._prev_time == int(self._now()):
            return self._prev_counters

        ops = []
        for type in self.types:
            ops.append(_SampleMethod[type]())

        now = self._now()
        genwindows = iter(self.windows)
        window = next(genwindows)
        result = {}
        done = False

        def _saveCounterValues(window):
            """Re-usable helper function for setting results and continuing"""

            prefix = ''
            if self.name is not None:
                prefix = self.name + '.'

            for op in ops:
                result[prefix + op.suffix + '.' + str(window)] = \
                    op.getvalue()
            # Move to the next window
            try:
                return next(genwindows), False
            except StopIteration:
                # We exhausted all our windows
                return None, True

        for ts, value in reversed(self.samples):
            # We exceeded the current window
            while not done and now - window > ts:
                # Save counter values
                window, done = _saveCounterValues(window)

            if done:
                # TODO: "prune" any remaining samples
                break

            for op in ops:
                op.add(value)

        # We exhausted the samples before the windows
        while not done:
            window, done = _saveCounterValues(window)

        self._prev_counters = result
        self._prev_time = int(now)
        self.dirty = False
        return result

    def getCounter(self, name, default=None):
        return self.getCounters().get(name, default)

    def iterkeys(self):
        for type in self.types:
            for window in self.windows:
                yield self.name + '.' + type + '.' + str(window)
        # TODO: Infinite Windows


samples = Samples
