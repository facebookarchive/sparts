# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.vservice import VService
from sparts.tasks.twisted import TwistedReactorTask, TwistedTask
from sparts.sparts import option
import random

from twisted.words.protocols import irc
from twisted.internet.protocol import ClientFactory
from twisted.internet import threads


class SpamClient(irc.IRCClient):
    def signedOn(self):
        self.factory.task.logger.debug("signed on!")
        irc.IRCClient.signedOn(self)
        self.factory.task.do_spam(self)

    def privmsg(self, user, channel, message):
        irc.IRCClient.privmsg(self, user, channel, message)
        self.factory.task.logger.info("<%s:%s> %s", channel, user, message)


class SpamClientFactory(ClientFactory):
    protocol = SpamClient
    def __init__(self, task):
        self.task = task

    def buildProtocol(self, addr):
        proto = ClientFactory.buildProtocol(self, addr)
        proto.nickname = self.task.nickname
        proto.password = self.task.password
        proto.source_url = self.task.source_url
        return proto


class SpamTask(TwistedTask):
    """Spams a user with a random number every 10 seconds"""
    LOOPLESS = True
    host = option(default='irc.ubuntu.com', help='[%(default)s]')
    port = option(default=6667, type=int, help='[%(default)s]')

    spamuser = option('spamuser', default=None, type=str,
                      help='user to spam every n seconds')
    nickname = option('nickname', default='SpamChatBotService_SpamTask',
                      help='nick to use [%(default)s]')
    password = option('password', help='password (optional)')
    source_url = option('source-url', default='http://github.com/fmoo/sparts',
                        help='source code URI [%(default)s]')

    connector = None

    def initTask(self):
        super(SpamTask, self).initTask()
        assert self.spamuser is not None

    def start(self):
        self.client_factory = SpamClientFactory(self)
        self.connector = threads.blockingCallFromThread(
            self.reactor,
            self.reactor.connectTCP,
            self.host,
            self.port,
            self.client_factory,
            timeout=5.0
        )

    def stop(self):
        if self.connector is not None:
            self.reactor.callFromThread(self.connector.disconnect)

    def do_spam(self, client):
        spam = str(random.random())
        self.logger.debug("sending spam (%s) to %s", spam, self.spamuser)
        client.msg(self.spamuser, spam)
        self.reactor.callLater(10.0, self.do_spam, client)

class SpamChatBotService(VService):
    TASKS=[TwistedReactorTask, SpamTask]

if __name__ == '__main__':
    SpamChatBotService.initFromCLI()
