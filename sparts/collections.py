from six.moves.queue import Queue
import heapq

class PriorityQueue(Queue):
    """A Queue subclass that uses `heapq` to maintain a priority queue"""

    def _init(self, maxsize):
        self.queue = []

    def _put(self, item):
        heapq.heappush(self.queue, item)

    def _get(self):
        return heapq.heappop(self.queue)
