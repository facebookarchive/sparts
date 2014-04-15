# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tests.base import BaseSpartsTestCase
from sparts import counters

import time

class CounterTests(BaseSpartsTestCase):
    def testSum(self):
        c = counters.Sum()
        self.assertEquals(c(), 0.0)
        c.increment()
        self.assertEquals(c(), 1.0)
        c.incrementBy(10)
        self.assertEquals(c(), 11.0)
        c.add(10)
        self.assertEquals(c(), 21.0)

    def testCount(self):
        c = counters.Count()
        self.assertEquals(c(), 0)
        c.add(100)
        self.assertEquals(c(), 1)

    def testMax(self):
        c = counters.Max()
        self.assertIs(c(), None)
        c.add(-10)
        self.assertEquals(c(), -10)
        c.add(-20)
        self.assertEquals(c(), -10)
        c.add(20)
        self.assertEquals(c(), 20)

    def testSampleNames(self):
        c = counters.samples(name='foo',
            types=[counters.SampleType.COUNT], windows=[100])
        c.add(1)
        self.assertEquals(c.getCounter('foo.count.100'), 1)

        c = counters.samples(
            types=[counters.SampleType.COUNT], windows=[100])
        c.add(1)
        self.assertEquals(c.getCounter('count.100'), 1)

    def testSamples(self):
        c = counters.samples(
            types=[counters.SampleType.COUNT, counters.SampleType.SUM],
            windows=[100, 1000])

        now = time.time()
        c._now = self.mock.Mock()

        # At t=0, add two values of 10.0
        c._now.return_value = now
        c.add(10.0)
        c.add(10.0)

        self.assertEquals(c.getCounter('count.100'), 2)
        self.assertEquals(c.getCounter('count.1000'), 2)
        self.assertEquals(c.getCounter('sum.100'), 20.0)
        self.assertEquals(c.getCounter('sum.1000'), 20.0)

        # At t=10, add one values of 10.0
        c._now.return_value = now + 10
        c.add(10.0)

        self.assertEquals(c.getCounter('count.100'), 3)
        self.assertEquals(c.getCounter('count.1000'), 3)
        self.assertEquals(c.getCounter('sum.100'), 30.0)
        self.assertEquals(c.getCounter('sum.1000'), 30.0)

        # At t=101, 2 values should have fallen out of the 100 window
        c._now.return_value = now + 101

        self.assertEquals(c.getCounter('count.100'), 1)
        self.assertEquals(c.getCounter('count.1000'), 3)
        self.assertEquals(c.getCounter('sum.100'), 10.0)
        self.assertEquals(c.getCounter('sum.1000'), 30.0)

        # At t=1001, all values should be gone from the 100 window,
        # but one value should remain in the 1000 window
        c._now.return_value = now + 1001

        self.assertEquals(c.getCounter('count.100'), 0)
        self.assertEquals(c.getCounter('count.1000'), 1)
        self.assertEquals(c.getCounter('sum.100'), 0.0)
        self.assertEquals(c.getCounter('sum.1000'), 10.0)

        # At t=1011, all values should be gone from all windows.
        c._now.return_value = now + 1011

        self.assertEquals(c.getCounter('count.100'), 0)
        self.assertEquals(c.getCounter('count.1000'), 0, str((now, c.samples)))
        self.assertEquals(c.getCounter('sum.100'), 0.0)
        self.assertEquals(c.getCounter('sum.1000'), 0.0)

