# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.sparts import option
from sparts.vtask import ExecuteContext, VTask
from sparts.tests.base import BaseSpartsTestCase, SingleTaskTestCase

class ExecuteContextTests(BaseSpartsTestCase):
    def test_comparisons(self):
        self.assertEqual(ExecuteContext(), ExecuteContext())
        self.assertEqual(ExecuteContext(item=10), ExecuteContext(item=10))
        self.assertNotEqual(ExecuteContext(), ExecuteContext(item=4))
        self.assertNotEqual(ExecuteContext(item=3), ExecuteContext(item=4))
        self.assertLess(ExecuteContext(item=0), ExecuteContext(item=10))
        self.assertGreater(ExecuteContext(item=10), ExecuteContext(item=0))


class VTaskOptionTests(SingleTaskTestCase):
    class TASK(VTask):
        LOOPLESS = True

        basicopt = option(default="spam")
        opt_uscore = option(default="eggs")
        opt_uscore2 = option(default="ham")

    def test_options(self):
        self.assertEqual(self.task.basicopt, "spam")
        self.assertEqual(self.task.opt_uscore, "eggs")
        self.assertEqual(self.task.opt_uscore2, "ham")


class VTaskOptionOverrideTests(SingleTaskTestCase):
    class TASK(VTask):
        LOOPLESS = True

        basicopt = option(default="spam")
        opt_uscore = option(default="eggs")
        opt_uscore2 = option(name="opt_uscore2", default="ham")

    def getCreateArgs(self):
        return [
            '--TASK-basicopt', 'foo',
            '--TASK-opt-uscore', 'bar',
            '--TASK-opt-uscore2', 'baz',
        ]

    def test_options(self):
        self.assertEqual(self.task.basicopt, "foo")
        self.assertEqual(self.task.opt_uscore, "bar")
        self.assertEqual(self.task.opt_uscore2, "baz")


class VTaskOptionPrefixTests(SingleTaskTestCase):
    class TASK(VTask):
        LOOPLESS = True
        OPT_PREFIX = 'my_task'

        basicopt = option(default="spam")
        opt_uscore = option(default="eggs")
        opt_uscore2 = option(name="opt_uscore2", default="ham")

    def test_options(self):
        self.assertEqual(self.task.basicopt, "spam")
        self.assertEqual(self.task.opt_uscore, "eggs")
        self.assertEqual(self.task.opt_uscore2, "ham")


class VTaskOptionPrefixOverrideTests(SingleTaskTestCase):
    class TASK(VTask):
        LOOPLESS = True
        OPT_PREFIX = 'my_task'

        basicopt = option(default="spam")
        opt_uscore = option(default="eggs")
        opt_uscore2 = option(name="opt_uscore2", default="ham")

    def getCreateArgs(self):
        return [
            '--my-task-basicopt', 'foo',
            '--my-task-opt-uscore', 'bar',
            '--my-task-opt-uscore2', 'baz',
        ]

    def test_options(self):
        self.assertEqual(self.task.basicopt, "foo")
        self.assertEqual(self.task.opt_uscore, "bar")
        self.assertEqual(self.task.opt_uscore2, "baz")
