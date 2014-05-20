# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
"""Module that provides an API for executing and managing child processes."""
from __future__ import absolute_import

from sparts.counters import counter
from sparts.sparts import option

from twisted.internet.protocol import ProcessProtocol
from twisted.protocols.basic import LineReceiver
from sparts.tasks.twisted import TwistedTask

import functools
import signal
import six
import time
import twisted.python.threadable
import twisted.internet.threads


class CommandTask(TwistedTask):
    """A task that provides a useful API for executing other commands.

    Python's Popen() can be hard to use, especially if you are executing long
    running child processes, and need to handle various stdout, stderr, and
    process exit events asynchronously.

    This particular implementation relies on Twisted's ProcessProtocol, but it
    wraps it in a way that makes it mostly opaque.
    """
    LOOPLESS = True
    OPT_PREFIX = 'cmd'

    kill_timeout = option(type=float, default=10.0,
                          help="Default shutdown kill timeout for outstanding "
                               "commands [%(default)s]")
    started = counter()
    finished = counter()

    def run(self, command, on_stdout=None, on_stderr=None, on_exit=None,
            line_buffered=True, kill_timeout=None, env=None):
        """Call this function to start a new child process running `command`.
        
        Additional callbacks, such as `on_stdout`, `on_stderr`, and `on_exit`,
        can be provided, that will receive a variety of parameters on the
        appropriate events.

        Line buffering can be disabled by passing `line_buffered`=False.

        Also, a custom `kill_timeout` (seconds) may be set that overrides the
        task default, in the event that a shutdown is received and you want
        to allow more time for the command to shut down."""
        self.logger.debug("task starting %s...", command)
        if isinstance(command, six.string_types):
            command = command.split(" ")

        # wrap on_exit with helper to remove registered comments
        on_exit = functools.partial(self._procExited, on_exit)

        proto = _ProcessProtocolAdapter(on_stdout, on_stderr, on_exit,
                                       line_buffered=line_buffered)

        if twisted.python.threadable.isInIOThread():
            result = self.reactor.spawnProcess(proto, executable=command[0],
                                               args=command)
        else:
            result = twisted.internet.threads.blockingCallFromThread(
                self.reactor, self.reactor.spawnProcess, proto,
                executable=command[0], args=command, env=env)

        self.outstanding[result] = kill_timeout

        self.started.increment()
        return result

    def initTask(self):
        super(CommandTask, self).initTask()
        self.outstanding = {}

    def _procExited(self, on_exit, proto, trans, reason):
        self.logger.debug("%s closed for %s", trans, reason)
        if on_exit is not None:
            on_exit(reason)

        self.outstanding.pop(trans)

        self.finished.increment()
        return None

    def join(self):
        """Overridden to block for process workers to shutdown / be killed."""
        # TODO: Conditions instead of sleep polling?
        while len(self.outstanding) > 0:
            time.sleep(0.250)

    def _killOutstanding(self, trans):
        if trans in self.outstanding:
            self.logger.info("Sending SIGKILL to %s", trans)
            trans.signalProcess(signal.SIGKILL)

    def stop(self):
        # twisted is pretty smart; the default signal handlers it installs
        # propagate SIGTERM to its children, so while we don't need to manually
        # TERM, we might still need to set some kill timeouts
        super(CommandTask, self).stop()

        for trans, kill_timeout in self.outstanding.items():
            if kill_timeout is None:
                kill_timeout = self.kill_timeout

            self.logger.info("Enqueuing kill for %s in %.1fs",
                             trans, kill_timeout)
            args = (kill_timeout, self._killOutstanding, trans)
            if twisted.python.threadable.isInIOThread():
                self.reactor.callLater(*args)
            else:
                self.reactor.callFromThread(self.reactor.callLater, *args)

    def isDoneWithReactor(self):
        """Overridden to keep reactor running until all commands finish."""
        return len(self.outstanding) == 0

class _ProcessProtocolAdapter(ProcessProtocol):
    """ProcessProtocol that allows custom callbacks, buffering."""
    def __init__(self, on_stdout=None, on_stderr=None, on_exit=None,
                 line_buffered=True):

        self.line_buffered = line_buffered
        self.on_stdout = on_stdout or (lambda *args: None)
        self.on_stderr = on_stderr or (lambda *args: None)
        self.on_exit = on_exit or (lambda *args: None)

        if self.line_buffered:
            self.stdout_buffer = self._makeBuffer(self.on_stdout)
            self.stderr_buffer = self._makeBuffer(self.on_stderr)

    def _makeBuffer(self, callback):
        buf = LineReceiver()
        buf.delimiter = "\n"
        buf.lineReceived = lambda line: callback(self.transport, line)
        return buf

    def connectionMade(self):
        ProcessProtocol.connectionMade(self)
        self.original_pid = self.transport.pid

    def outReceived(self, data):
        if self.line_buffered:
            self.stdout_buffer.dataReceived(data)
        else:
            self.on_stdout(self.transport, data)

    def errReceived(self, data):
        if self.line_buffered:
            self.stderr_buffer.dataReceived(data)
        else:
            self.on_stderr(self.transport, data)

    def processEnded(self, reason):
        # Ugh, this is a hack... I need to pass self because Twisted unsets pid
        # after the process has exited, but I need the *old* pid to do proper
        # accounting.  *YES* I get why this is fundamentally broken
        self.on_exit(self, self.transport, reason)
        self.transport.loseConnection()
