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
        self.consumer = self.service.requireTask(Consumer)

    def execute(self, *args, **kwargs):
        for i in xrange(5):
            item = random.random()
            self.consumer.queue.put(item)
            self.logger.info("Producer put %s into queue", item)


class ProducerConsumer(VService):
    TASKS=[Producer]


if __name__ == '__main__':
    ProducerConsumer.initFromCLI()
