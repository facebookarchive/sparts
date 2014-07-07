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

        # Put an old duplicate back in it, make sure it's not empty again
        queue.put(0)
        self.assertFalse(queue.empty())

        # Set "explicit_unsee" mode to verify some of that behavior, and go
        # back to silent discards for brevity.
        queue.silent = True
        queue.explicit_unsee = True

        # Remove the item we just inserted.  Things should be empty.
        queue.get()
        self.assertTrue(queue.empty())

        # Because we didn't explicitly unsee, the 0 should be discarded
        # instead of re-queued, and the queue should remain empty.
        queue.put(0)
        self.assertTrue(queue.empty())

        # Now, explicitly unsee, and re-queue.  It should succeed.
        queue.unsee(0)
        queue.put(0)
        self.assertFalse(queue.empty())
