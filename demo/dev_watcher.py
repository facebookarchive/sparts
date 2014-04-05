from sparts.tasks.file import DirectoryWatcherTask
from sparts.vservice import VService


class DevWatcher(DirectoryWatcherTask):
    INTERVAL = 1.0
    PATH = '/dev'

DevWatcher.register()


if __name__ == '__main__':
    VService.initFromCLI()
