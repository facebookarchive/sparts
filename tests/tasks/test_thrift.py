# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from __future__ import absolute_import

from sparts.tests.base import SingleTaskTestCase, Skip

try:
    from sparts.tasks.thrift import ThriftHandlerTask
    from sparts.gen.fb303 import FacebookService
except ImportError:
    raise Skip("Need thrift language bindings to run this test")


class IncompleteHandler(ThriftHandlerTask):
    MODULE = FacebookService


class IncompleteHandlerTest(SingleTaskTestCase):
    TASK = IncompleteHandler

    def setUp(self):
        with self.assertRaises(Exception):
            super(IncompleteHandlerTest, self).setUp()

    def test_nothing(self):
        self.assertTrue(True)
