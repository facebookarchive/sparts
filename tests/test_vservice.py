# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.sparts import option
from sparts.tests.base import ServiceTestCase
from sparts.vservice import VService

class VServiceTests(ServiceTestCase):
    def test_verifyCustomName(self):
        self.assertEqual(self.service.name, 'VService')
        self.assertEqual(self.service._name, 'VService')
        self.service.name = 'MyService'
        self.assertEqual(self.service.name, 'MyService')
        self.assertEqual(self.service._name, 'MyService')

    def testRegisterClearWarnings(self):
        self.assertEmpty(self.service.getWarnings())
        wid = self.service.registerWarning('Oops!  Something went wrong.')
        self.assertNotEmpty(self.service.getWarnings())
        self.assertFalse(self.service.clearWarning(wid + 1))
        self.assertTrue(self.service.clearWarning(wid))
        self.assertEmpty(self.service.getWarnings())

        wid = self.service.registerWarning('Oops!  Something else went wrong.')
        self.assertNotEmpty(self.service.getWarnings())
        self.service.clearWarnings()
        self.assertEmpty(self.service.getWarnings())

    def testExportedValues(self):
        service = self.service

        self.assertEmpty(service.getExportedValues())
        self.assertEqual(service.getExportedValue('notexists'), '')

        # Set some values
        service.setExportedValue('foo', 'bar')
        service.setExportedValue('spam', 'eggs')
        service.setExportedValue('ham', 'eggs')

        # Verify we got something back this time
        self.assertNotEmpty(service.getExportedValues())

        # Verify getExportedValue with real values
        self.assertEqual(service.getExportedValue('foo'), 'bar')
        self.assertEqual(service.getExportedValue('spam'), 'eggs')

        # Verify Regex API
        k_v = service.getRegexExportedValues('.*am')
        self.assertEqual(len(k_v), 2)
        self.assertNotContains('foo', k_v)
        self.assertContains('spam', k_v)
        self.assertContains('ham', k_v)

        # Verify Selected API
        k_v = service.getSelectedExportedValues(['notexists', 'ham', 'spam'])
        self.assertEqual(len(k_v), 3)
        self.assertNotContains('foo', k_v)

        # Verify keys
        self.assertContains('notexists', k_v)
        self.assertContains('spam', k_v)
        self.assertContains('ham', k_v)

        # Verify values
        self.assertEqual(k_v['notexists'], '')
        self.assertEqual(k_v['spam'], 'eggs')
        self.assertEqual(k_v['ham'], 'eggs')

        # Verify deletion
        service.setExportedValue('ham', None)
        values = service.getExportedValues()
        self.assertNotEmpty(values)
        self.assertEqual(len(values), 2)
        self.assertContains('foo', values)
        self.assertContains('spam', values)
        self.assertNotContains('ham', values)


class VServiceOptionTests(ServiceTestCase):
    def getServiceClass(self):
        class MYSERVICE(VService):
            basicopt = option(default="spam")
            opt_uscore = option(default="eggs")
            opt_uscore2 = option(name="opt_uscore2", default="ham")
        return MYSERVICE

    def test_options(self):
        self.assertEqual(self.service.basicopt, "spam")
        self.assertEqual(self.service.opt_uscore, "eggs")
        self.assertEqual(self.service.opt_uscore2, "ham")


class VServiceOptionOverrideTests(ServiceTestCase):
    def getServiceClass(self):
        class MYSERVICE(VService):
            basicopt = option(default="spam")
            opt_uscore = option(default="eggs")
            opt_uscore2 = option(name="opt_uscore2", default="ham")
        return MYSERVICE

    def getCreateArgs(self):
        return [
            '--basicopt', 'foo',
            '--opt-uscore', 'bar',
            '--opt-uscore2', 'baz',
        ]

    def test_options(self):
        self.assertEqual(self.service.basicopt, "foo")
        self.assertEqual(self.service.opt_uscore, "bar")
        self.assertEqual(self.service.opt_uscore2, "baz")
