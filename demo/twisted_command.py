# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant 
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.tasks.twisted_command import CommandTask
from sparts.tasks.periodic import PeriodicTask
from sparts.vservice import VService

CommandTask.register()

def on_stdout(trans, data):
    print "WOOT %s: %s" % (trans, data)

class SpawnHelloWorldTask(PeriodicTask):
    INTERVAL = 2
    DEPS = [CommandTask]

    def execute(self):
        t = self.service.tasks.CommandTask
        c = t.run('sleep 5')
        self.logger.debug("PeriodicTask spawned %s", c)

SpawnHelloWorldTask.register()

if __name__ == '__main__':
    VService.initFromCLI()
