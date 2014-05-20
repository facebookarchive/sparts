# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from six.moves import xrange
from sparts.tasks.periodic import PeriodicTask
from sparts.tasks.queue import QueueTask
from sparts.vservice import VService
import random
import threading


class Consumer(QueueTask):
    WORKERS = 10

    def execute(self, item, context):
        self.logger.info("[%s] Got %s", threading.current_thread().name, item)


class Producer(PeriodicTask):
    INTERVAL = 1.0
    DEPS = [Consumer]

    def initTask(self):
        super(Producer, self).initTask()
        self.consumer = self.service.tasks.Consumer

    def execute(self, *args, **kwargs):
        for i in xrange(5):
            item = random.random()
            self.consumer.queue.put(item)
            self.logger.info("Producer put %s into queue", item)


class ProducerConsumer(VService):
    TASKS=[Producer]


if __name__ == '__main__':
    ProducerConsumer.initFromCLI()
