# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.collections import PriorityQueue
from sparts.tests.base import BaseSpartsTestCase

class PriotityQueueTests(BaseSpartsTestCase):
    def test_basic_functionality(self):
        # Make a priority queue
        queue = PriorityQueue()

        # It should be empty
        self.assertTrue(queue.empty())

        # Put a bunch of stuff in it.
        queue.put(3.14159)
        queue.put(3)
        queue.put(1)
        queue.put(6)
        queue.put(-21)
        queue.put(0)

        # Not empty any more
        self.assertFalse(queue.empty())

        # Remove stuff in sorted order
        self.assertEquals(queue.get(), -21)
        self.assertEquals(queue.get(), 0)
        self.assertEquals(queue.get(), 1)
        self.assertEquals(queue.get(), 3)
        self.assertEquals(queue.get(), 3.14159)
        self.assertEquals(queue.get(), 6)

        # It should be empty again
        self.assertTrue(queue.empty())
