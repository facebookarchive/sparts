from .fb303 import FacebookService
from .fb303.FacebookBase import FacebookBase as _FacebookBase


class FacebookBase(_FacebookBase, FacebookService.Processor):
    THRIFT = FacebookService

    def __init__(self):
        _FacebookBase.__init__(self, self.__class__.__name__)
        FacebookService.Processor.__init__(self, self)
