# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.vtask import ExecuteContext
from sparts.tests.base import BaseSpartsTestCase

class ExecuteContextTests(BaseSpartsTestCase):
    def test_comparisons(self):
        self.assertEqual(ExecuteContext(), ExecuteContext())
        self.assertEqual(ExecuteContext(item=10), ExecuteContext(item=10))
        self.assertNotEqual(ExecuteContext(), ExecuteContext(item=4))
        self.assertNotEqual(ExecuteContext(item=3), ExecuteContext(item=4))
        self.assertLess(ExecuteContext(item=0), ExecuteContext(item=10))
        self.assertGreater(ExecuteContext(item=10), ExecuteContext(item=0))
