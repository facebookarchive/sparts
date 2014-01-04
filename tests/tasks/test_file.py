from sparts.tasks.file import DirectoryWatcherTask
from ..base import SingleTaskTestCase 
from tempfile import mkdtemp
from shutil import rmtree
from mock import Mock
import os.path
import time


class MyTask(DirectoryWatcherTask):
    def __init__(self, *args, **kwargs):
        super(MyTask, self).__init__(*args, **kwargs) 
        self.onFileCreated = Mock()
        self.onFileDeleted = Mock()
        self.onFileChanged = Mock()

class TestMyTask(SingleTaskTestCase):
    TASK = MyTask

    def setUp(self):
        self.testpath = mkdtemp()
        MyTask.PATH = self.testpath
        MyTask.INTERVAL = 0.25
        super(TestMyTask, self).setUp()
        self.task.execute()

    def tearDown(self):
        rmtree(self.testpath)
        super(TestMyTask, self).tearDown()

    def test_file_create(self):
        fn = os.path.join(self.testpath, 'foo')
        with open(fn, mode='w'):
            pass
        # Sleep one second so that mtime/atime will change appropriately
        time.sleep(1.0)
        os.utime(fn, None)
        self.task.execute()
        self.assertTrue(self.task.onFileCreated.called)
        self.assertEquals(self.task.onFileCreated.call_count, 1)
        self.assertEquals(self.task.onFileCreated.call_args[0][0], 'foo',
                          self.task.onFileCreated.call_args)

    def test_file_delete(self):
        self.test_file_create()
        os.remove(os.path.join(self.testpath, 'foo'))
        self.task.execute()

        self.assertTrue(self.task.onFileDeleted.called)
        self.assertEquals(self.task.onFileDeleted.call_count, 1)
        self.assertEquals(self.task.onFileDeleted.call_args[0][0], 'foo',
                          self.task.onFileDeleted.call_args)

    def test_file_update(self):
        self.test_file_create()
        os.utime(os.path.join(self.testpath, 'foo'), None)
        self.task.execute()
        self.assertTrue(self.task.onFileChanged.called)
        self.assertEquals(self.task.onFileChanged.call_count, 1)
        self.assertEquals(self.task.onFileChanged.call_args[0][0], 'foo',
                          self.task.onFileChanged.call_args)
