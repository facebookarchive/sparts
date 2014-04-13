# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from .base import BaseSpartsTestCase
from sparts import ctx

class ContextTests(BaseSpartsTestCase):
    def testTmpdir(self):
        with ctx.tmpdir() as path:
            path_copy = path
            self.assertExists(path)

        self.assertNotExists(path_copy)

    def testAddPath(self):
        import sys
        with ctx.tmpdir() as path:
            self.assertNotIn(path, sys.path)
            with ctx.add_path(path):
                self.assertIn(path, sys.path)
            self.assertNotIn(path, sys.path)

