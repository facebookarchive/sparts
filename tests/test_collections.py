# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.collections import PriorityQueue, UniqueQueue, Duplicate
from sparts.tests.base import BaseSpartsTestCase


class PriorityQueueTests(BaseSpartsTestCase):
    def test_basic_functionality(self):
        # Make a priority queue
        queue = PriorityQueue()

        # It should be empty
        self.assertTrue(queue.empty())

        # Put a bunch of stuff in it.
        queue.put(0)
        queue.put(3.14159)
        queue.put(3)
        queue.put(1)
        queue.put(6)
        queue.put(-21)
        queue.put(0)

        # Not empty any more
        self.assertFalse(queue.empty())

        # Remove stuff in sorted order
        self.assertEqual(queue.get(), -21)
        self.assertEqual(queue.get(), 0)
        self.assertEqual(queue.get(), 0)
        self.assertEqual(queue.get(), 1)
        self.assertEqual(queue.get(), 3)
        self.assertEqual(queue.get(), 3.14159)
        self.assertEqual(queue.get(), 6)

        # It should be empty again
        self.assertTrue(queue.empty())


class UniqueQueueTests(BaseSpartsTestCase):
    def test_basic_functionality(self):
        # Make a priority queue
        queue = UniqueQueue()

        # It should be empty
        self.assertTrue(queue.empty())

        # Put some stuff in it.  Use `silent` mode for brevity.
        queue.silent = True
        queue.put(2)
        queue.put(0)
        queue.put(2)
        queue.put(1)

        # Make sure the non-silent API causes the class to throw.
        queue.silent = False
        with self.assertRaises(Duplicate):
            queue.put(0)

        # Not empty any more
        self.assertFalse(queue.empty())

        # Remove stuff
        self.assertEqual(queue.get(), 2)
        self.assertEqual(queue.get(), 0)
        self.assertEqual(queue.get(), 1)

        # It should be empty again
        self.assertTrue(queue.empty())
