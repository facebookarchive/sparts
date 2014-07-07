import heapq

from six.moves.queue import Queue


class PriorityQueue(Queue):
    """A Queue subclass that uses `heapq` to maintain a priority queue"""

    def _init(self, maxsize):
        self.queue = []

    def _put(self, item):
        heapq.heappush(self.queue, item)

    def _get(self):
        return heapq.heappop(self.queue)


class Duplicate(Exception):
    pass


class UniqueQueue(Queue):
    """A Queue subclass that uses a set to prevent duplicate inserts.

    On duplicate insert the `Duplicate` exception will be thrown.  The
    `silent` attribute may be set to True, in order to change this
    behavior to silently discard the duplicates instead of raising."""
    def _init(self, maxsize):
        Queue._init(self, maxsize)
        self._seen = set()
        self._discards = 0
        self.silent = False
        self.explicit_unsee = False

    def _put(self, item):
        if item in self._seen:
            self._discards += 1

            # Handle
            if self.silent:
                return
            else:
                raise Duplicate

        Queue._put(self, item)
        self._seen.add(item)

    def _get(self):
        item = Queue._get(self)
        if not self.explicit_unsee:
            self._seen.remove(item)
        return item

    def unsee(self, item):
        if not self.explicit_unsee:
            return

        with self.mutex:
            self._seen.remove(item)
