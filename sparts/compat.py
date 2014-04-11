import sys

if sys.version < '3':
    def iteritems(d):
        return d.iteritems()
    def itervalues(d):
        return d.itervalues()
    xrange = xrange
    import Queue as queue
    from urllib2 import urlopen

else:
    def iteritems(d):
        return d.items()
    def itervalues(d):
        return d.values()
    def xrange(it):
        return range(it)
    import queue
    from urllib.request import urlopen

try:
    from collections import OrderedDict
except NameError:
    from ordereddict import OrderedDict
