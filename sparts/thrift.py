from __future__ import absolute_import

from thrift.transport.TSocket import TSocket
from thrift.transport.TTransport import TFramedTransport
from thrift.protocol.TBinaryProtocol import TBinaryProtocol

from functools import partial


class ThriftClient(object):
    MODULE = None
    HOST = None
    PORT = None
    TRANSPORT_CLASS = TFramedTransport
    PROTOCOL_CLASS = TBinaryProtocol
    SOCKET = TSocket
    CONNECT_TIMEOUT = 3.0

    @classmethod
    def for_hostport(cls, host=None, port=None, **kwargs):
        assert host or cls.HOST, "You must define a host!"
        assert port or cls.PORT, "You must define a port!"
        return cls(host=host, port=port, **kwargs)

    @classmethod
    def for_localhost(cls, port=None, **kwargs):
        assert port or cls.PORT, "You must define a port!"
        return cls(host='127.0.0.1', port=port, **kwargs)

    def _initAttribute(self, name, value, default):
        if value is None:
            value = default
        setattr(self, name, value)

    def __init__(self, host=None, port=None, module=None, lazy=True,
                 connect_timeout=None, transport_class=None,
                 protocol_class=None):

        self._initAttribute('host', host, self.HOST)
        self._initAttribute('port', port, self.PORT)
        self._initAttribute('module', module, self.MODULE)
        self._initAttribute('connect_timeout', connect_timeout,
                            self.CONNECT_TIMEOUT)
        self._initAttribute('transport_class', transport_class,
                            self.TRANSPORT_CLASS)
        self._initAttribute('protocol_class', protocol_class,
                            self.PROTOCOL_CLASS)
        self.lazy = lazy

        assert self.module is not None, "You must define a thrift module!"

        if self.lazy:
            self._client = None
        else:
            self._connect()

    def _connect(self):
        # TODO: Add some kind of support for HTTP or SSLSocket
        self._socket = TSocket(self.host, self.port)
        self._socket.setTimeout(int(self.connect_timeout * 1000))
        self._transport = self.transport_class(self._socket)
        self._protocol = self.protocol_class(self._transport)
        self._client = self.module.Client(self._protocol)
        self._transport.open()

    def _lazyCall(self, name, *args, **kwargs):
        if self._client is None:
            self._connect()
        # TODO: Automatically connect on timed out connections
        return getattr(self._client, name)(*args, **kwargs)

    def __getattr__(self, name):
        getattr(self.module.Client, name)
        return partial(self._lazyCall, name)
