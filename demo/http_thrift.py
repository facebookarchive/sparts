from sparts.vservice import VService
from sparts.tasks.thrift import NBServerTask
from sparts.tasks.fb303 import FB303ProcessorTask
from sparts.tasks.tornado import TornadoHTTPTask, TornadoIOLoopTask
from sparts.tasks.tornado_thrift import TornadoThriftHandler


class MyHTTPTask(TornadoHTTPTask):
    def getApplicationConfig(self):
        return [
            ('/thrift', TornadoThriftHandler, dict(processor=self.service)),
        ]

class MyHTTPThriftService(VService):
    TASKS=[NBServerTask, MyHTTPTask, TornadoIOLoopTask, FB303ProcessorTask]


if __name__ == '__main__':
    MyHTTPThriftService.initFromCLI()
