# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tests.base import BaseSpartsTestCase
from sparts import ctx

import os
import os.path
import sys

class ContextTests(BaseSpartsTestCase):
    def testTmpdir(self):
        """Verify `ctx.tmpdir`"""
        with ctx.tmpdir() as path:
            path_copy = path
            self.assertExists(path)

        self.assertNotExists(path_copy)

    def testAddPath(self):
        """Verify `ctx.add_path`"""
        # Create a temp directory
        with ctx.tmpdir() as path:
            # The temp dir should not be in the path yet.
            self.assertNotIn(path, sys.path)

            with ctx.add_path(path):
                # Now it should be in the path
                self.assertIn(path, sys.path)

            # After exiting the context, it should be gone again
            self.assertNotIn(path, sys.path)

    def assertSamePath(self, a, b, msg=''):
        self.assertEqual(os.path.realpath(a),
                         os.path.realpath(b), msg)

    def assertDifferentPath(self, a, b, msg=''):
        self.assertNotEqual(os.path.realpath(a),
                            os.path.realpath(b), msg)

    def testChdir(self):
        """Verify `ctx.chdir`"""
        with ctx.tmpdir() as path:
            orig_dir = os.getcwd()

            # Make sure we're not in the new tmpdir.  This should be impossible.
            self.assertDifferentPath(orig_dir, path)

            with ctx.chdir(path):
                # Make sure we changed correctly
                self.assertSamePath(os.getcwd(), path)

            # Make sure we're not there anymore
            self.assertDifferentPath(os.getcwd(), path)

            # Make sure we returned to the original location
            self.assertSamePath(os.getcwd(), orig_dir)

    def testModuleSnapshot(self):
        """Verify `ctx.module_snapshot`"""
        # Make sure this module hasn't been imported yet.  This should never
        # be used by this unittest.
        self.assertNotIn('sparts.tests.dummy', sys.modules)

        with ctx.module_snapshot():
            # Import the module
            import sparts.tests.dummy
            self.assertIn('sparts.tests.dummy', sys.modules)
            self.assertIs(sys.modules['sparts.tests.dummy'], sparts.tests.dummy)

        # Make sure it's been removed
        self.assertNotIn('sparts.tests.dummy', sys.modules)

