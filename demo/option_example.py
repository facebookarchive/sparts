from sparts.tasks.periodic import PeriodicTask
from sparts.vservice import VService
from sparts.sparts import option
import socket

class HostCheckTask(PeriodicTask):
    INTERVAL=5
    check_name = option('check-name', default=socket.getfqdn(), type=str,
                        help='Name to check [%(default)s]')
    def execute(self, *args, **kwargs):
        self.logger.info("LOOKUP %s => %s", self.check_name,
                         socket.gethostbyname(self.check_name))


class DNSChecker(VService):
    TASKS=[HostCheckTask]


if __name__ == '__main__':
    DNSChecker.initFromCLI()
