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


class UniqueQueue(Queue):
    """A Queue subclass that uses a set to prevent duplicate inserts"""
    def _init(self, maxsize):
        Queue._init(self, maxsize)
        self._seen = set()
        self._discards = 0

    def _put(self, item):
        if item in self._seen:
            self._discards += 1
            return

        Queue._put(self, item)
        self._seen.add(item)

    def _get(self):
        item = Queue._get(self)
        self._seen.remove(item)
        return item
