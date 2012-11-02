from sparts.vservice import VService
from sparts.tasks.thrift import NBServerTask
from sparts.tasks.tornado import TornadoHTTPTask, TornadoIOLoopTask
from sparts.tasks.tornado_thrift import TornadoThriftHandler
from sparts.vfb303 import FacebookBase


class MyHTTPTask(TornadoHTTPTask):
    def getApplicationConfig(self):
        return [
            ('/thrift', TornadoThriftHandler, dict(processor=self.service)),
        ]

class MyHTTPThriftService(VService, FacebookBase):
    TASKS=[NBServerTask, MyHTTPTask, TornadoIOLoopTask]

    def __init__(self, *args, **kwargs):
        VService.__init__(self, *args, **kwargs)
        FacebookBase.__init__(self)


if __name__ == '__main__':
    MyHTTPThriftService.initFromCLI()
