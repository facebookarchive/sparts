from sparts.vservice import VService
from sparts.tasks.thrift import NBServerTask
from sparts.tasks.fb303 import FB303ProcessorTask
from sparts.tasks.tornado import TornadoHTTPTask, TornadoIOLoopTask
from sparts.tasks.tornado_thrift import TornadoThriftHandler

NBServerTask.register()
TornadoIOLoopTask.register()
FB303ProcessorTask.register()


class MyHTTPTask(TornadoHTTPTask):
    DEPS = [FB303ProcessorTask]

    def getApplicationConfig(self):
        return [
            ('/thrift', TornadoThriftHandler,
                dict(processor=self.service.requireTask(FB303ProcessorTask))),
        ]

MyHTTPTask.register()


if __name__ == '__main__':
    VService.initFromCLI()
