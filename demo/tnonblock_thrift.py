from sparts.vservice import VService
from sparts.tasks.thrift import NBServerTask
from sparts.tasks.fb303 import FB303ProcessorTask

NBServerTask.register()
FB303ProcessorTask.register()


if __name__ == '__main__':
    VService.initFromCLI()
