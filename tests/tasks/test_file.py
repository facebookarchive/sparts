# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from sparts.fileutils import NamedTemporaryDirectory
from sparts.tests.base import SingleTaskTestCase
from sparts.tasks.file import DirectoryWatcherTask
from shutil import rmtree

import errno
import os.path


class MyTask(DirectoryWatcherTask):
    def __init__(self, *args, **kwargs):
        super(MyTask, self).__init__(*args, **kwargs)
        self.onFileCreated = self.service.test.mock.Mock()
        self.onFileDeleted = self.service.test.mock.Mock()
        self.onFileChanged = self.service.test.mock.Mock()

class TestMyTask(SingleTaskTestCase):
    TASK = MyTask

    def setUp(self):
        self.testpath = NamedTemporaryDirectory()
        MyTask.PATH = self.testpath.name
        MyTask.INTERVAL = 0.25
        super(TestMyTask, self).setUp()
        self.task.execute()

    def tearDown(self):
        self.testpath.close()
        super(TestMyTask, self).tearDown()

    def test_file_create(self):
        fn = self.testpath.join('foo')
        with open(fn, mode='w'):
            pass
        os.utime(fn, None)
        self.task.execute()
        self.assertTrue(self.task.onFileCreated.called)
        self.assertEqual(self.task.onFileCreated.call_count, 1)
        self.assertEqual(self.task.onFileCreated.call_args[0][0], 'foo',
                         self.task.onFileCreated.call_args)

    def test_file_delete(self):
        self.test_file_create()
        os.remove(self.testpath.join('foo'))
        self.task.execute()

        self.assertTrue(self.task.onFileDeleted.called)
        self.assertEqual(self.task.onFileDeleted.call_count, 1)
        self.assertEqual(self.task.onFileDeleted.call_args[0][0], 'foo',
                          self.task.onFileDeleted.call_args)

    def test_file_update(self):
        self.test_file_create()

        self.task.execute()
        path = self.testpath.join('foo')

        # Run once to make sure we detect the current time for the files
        self.task.execute()

        # Forcibly update the atime/mtime of the file
        st = os.stat(path)
        self.task.stat = self.mock.Mock()
        self.task.stat.return_value = self.mock.NonCallableMock(wraps=st)
        self.task.stat.return_value.st_atime = st.st_atime - 10
        self.task.stat.return_value.st_mtime = st.st_mtime - 10

        self.task.execute()
        self.task.stat.assert_called_with(path)

        st2 = self.task.stat()
        self.assertEqual(st2.st_atime, st.st_atime - 10)
        self.assertEqual(st2.st_mtime, st.st_mtime - 10)

        self.assertTrue(self.task.onFileChanged.called)
        self.assertEqual(self.task.onFileChanged.call_count, 1)
        self.assertEqual(self.task.onFileChanged.call_args[0][0], 'foo',
                         self.task.onFileChanged.call_args)

    def test_file_delete_race_condition(self):
        self.test_file_create()

        self.task.stat = self.mock.Mock()
        self.task.stat.side_effect = OSError(errno.ENOENT, 'Fake ENOENT')
        self.task.execute()

        self.assertTrue(self.task.onFileDeleted.called)

    def test_nodirectory_ok(self):
        # Call close() on the named directory to cleanup the directory
        self.testpath.close()

        # Then, call execute() and make sure nothing blows up
        self.task.execute()
