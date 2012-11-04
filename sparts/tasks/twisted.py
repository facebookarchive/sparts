from __future__ import absolute_import

from ..vtask import VTask, SkipTask

from twisted.internet import epollreactor
epollreactor.install()

import twisted.internet


class TwistedReactorTask(VTask):
    reactor = None

    def initTask(self):
        super(TwistedReactorTask, self).initTask()
        needed = getattr(self.service, 'REQUIRE_TWISTED', False)
        for t in self.service.tasks:
            if isinstance(t, TwistedTask):
                needed = True

        if not needed:
            raise SkipTask("No TwistedTasks found or enabled")

        self.reactor = twisted.internet.reactor

    def _runloop(self):
        self.reactor.run(installSignalHandlers=0)

    def stop(self):
        self.reactor.callFromThread(self.reactor.stop)


class TwistedTask(VTask):
    def initTask(self):
        super(TwistedTask, self).initTask()
        self.reactor_task = self.service.requireTask('TwistedReactorTask')

    @property
    def reactor(self):
        return self.reactor_task.reactor
