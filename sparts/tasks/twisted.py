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

    def start(self):
        # TODO: register signals manually using some 'clean' signal handler
        # chaining stuff
        self.reactor._handleSignals()
        super(TwistedReactorTask, self).start()

    def _runloop(self):
        self.reactor.run(installSignalHandlers=0)

    def stop(self):
        self._tryShutdown()

    def _tryShutdown(self):
        can_shutdown = True
        self.logger.debug('_tryShutdown with %d tasks', len(self.service.tasks))
        for t in self.service.tasks:
            if isinstance(t, TwistedTask):
                if not t.isDoneWithReactor():
                    self.logger.debug("%s is not done with the reactor", t.name)
                    can_shutdown = False
        if can_shutdown:
            self.reactor.callFromThread(self.reactor.stop)
        else:
            self.reactor.callFromThread(self.reactor.callLater, 0.3,
                                        self._tryShutdown)

class TwistedTask(VTask):
    DEPS = [TwistedReactorTask]

    def initTask(self):
        super(TwistedTask, self).initTask()
        self.reactor_task = self.service.requireTask('TwistedReactorTask')

    @property
    def reactor(self):
        return self.reactor_task.reactor

    def isDoneWithReactor(self):
        """Override this to handle shutdowns more gracefully"""
        return True
