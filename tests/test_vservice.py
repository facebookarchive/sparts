# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tests.base import ServiceTestCase

class VServiceTests(ServiceTestCase):
    def test_verifyCustomName(self):
        self.assertEquals(self.service.name, 'VService')
        self.assertEquals(self.service._name, 'VService')
        self.service.name = 'MyService'
        self.assertEquals(self.service.name, 'MyService')
        self.assertEquals(self.service._name, 'MyService')

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

