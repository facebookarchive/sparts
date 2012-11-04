from ..vtask import VTask, ExecuteContext, TryLater
from ..sparts import option
from Queue import Queue, Empty

class QueueTask(VTask):
    WORKERS = 1
    workers = option('workers', type=int, default=lambda cls: cls.WORKERS,
                     help='Number of threads to spawn to work on items from '
                          'its queue. [%(default)s]')

    def initTask(self):
        super(QueueTask, self).initTask()
        self.queue = Queue()

    def _runloop(self):
        while not self.service._stop:
            try:
                item = self.queue.get(timeout=0.600)
            except Empty:
                continue

            if isinstance(item, ExecuteContext):
                context = item
                item = context.item
            else:
                context = ExecuteContext(item=item)
            try:
                self.execute(item, context)
            except TryLater:
                context.attempt += 1
                self.queue.put(context)
            finally:
                self.queue.task_done()

    def execute(self, item, context):
        raise NotImplementedError()
