from ..vtask import VTask, ExecuteContext, TryLater
from ..sparts import option
from Queue import Queue, Empty

class QueueTask(VTask):
    WORKERS = 1
    workers = option('workers', type=int, default=lambda cls: cls.WORKERS,
                     help='Number of threads to spawn to work on items from '
                          'its queue. [%(default)s]')

    def execute(self, item, context):
        """Implement this in your QueueTask subclasses"""
        raise NotImplementedError()

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
                result = self.execute(item, context)
                if context.deferred is not None:
                    context.deferred.callback(result)
            except TryLater:
                context.attempt += 1
                self.queue.put(context)
            except Exception as ex:
                if context.deferred is not None:
                    self.unhandled = None
                    context.deferred.addErrback(self.unhandledErrback)
                    context.deferred.errback(ex)
                    if self.unhandled is not None:
                        self.unhandled.raiseException()
                else:
                    raise
            finally:
                self.queue.task_done()

    def unhandledErrback(self, error):
        self.unhandled = error
        return None


