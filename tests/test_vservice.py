from .base import ServiceTestCase

class VServiceTests(ServiceTestCase):
    def verifyCustomName(self):
        self.assertEquals(self.service.name, 'VService')
        self.assertEquals(self.service._name, 'VService')
        self.service.name = 'MyService'
        self.assertEquals(self.service.name, 'MyService')
        self.assertEquals(self.service._name, 'MyService')
