# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.counters import samples, SampleType
from sparts.sparts import option
from sparts.tasks.periodic import PeriodicTask
from sparts.vservice import VService
import socket

class HostCheckTask(PeriodicTask):
    INTERVAL = 5
    check_name = option(default=socket.getfqdn(), type=str,
                        help='Name to check [%(default)s]')

    def execute(self, *args, **kwargs):
        self.logger.info("LOOKUP %s => %s", self.check_name,
                         socket.gethostbyname(self.check_name))

class PrintCountersTask(PeriodicTask):
    INTERVAL = 6
    execute_duration = samples(windows=[60],
       types=[SampleType.MAX, SampleType.MIN])

    def execute(self, *args, **kwargs):
        hostcheck = self.service.tasks.HostCheckTask
        self.logger.info("hostcheck.duration :: %s",
                         hostcheck.execute_duration.getCounters())
        self.logger.info("this.duration :: %s",
                         self.execute_duration.getCounters())


class DNSChecker(VService):
    TASKS=[HostCheckTask, PrintCountersTask]


if __name__ == '__main__':
    DNSChecker.initFromCLI()
