# Copyright (c) 2014, Facebook, Inc.  All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from distutils.command.upload import upload as UploadCommand
from setuptools import setup, find_packages, Command
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.test import test as TestCommand

from distutils.spawn import find_executable
from glob import glob
import os.path
import imp
import subprocess
import sys


THRIFT = find_executable('thrift')

NAME = 'sparts'
ROOT = os.path.abspath(os.path.dirname(__file__))

def read(fname):
    """Read a file relative to the repository root"""
    return open(os.path.join(ROOT, fname)).read()

def exists(fname):
    """Returns True if `fname` relative to `ROOT` exists"""
    return os.path.exists(os.path.join(ROOT, fname))

def version():
    """Return the version number from sparts/__version__.py"""
    file, pathname, description = imp.find_module(NAME, [ROOT])
    return imp.load_module(NAME, file, pathname, description).__version__

# Initialize custom command handlers
cmdclass = {}

# These files are shadowed in the source repository from
# externals.  If you are developing sparts, you can use git submodule to make
# sure you have the latest/greatest fb303 from thrift.
WANT_COPY = {
    'externals/thrift/contrib/fb303/if/fb303.thrift':
        'thrift/fb303.thrift',
}

# Let's figure out which files exist in which submodules...
CAN_COPY = []
for src in WANT_COPY:
    if exists(src):
        CAN_COPY.append(src)


class submodule_copy(Command):
    user_options=[]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        for src in CAN_COPY:
            self.copy_file(os.path.join(ROOT, src),
                           os.path.join(ROOT, WANT_COPY[src]))

if CAN_COPY:
    cmdclass['submodule_copy'] = submodule_copy

# If we have a thrift compiler installed, let's use it to re-generate
# the .py files.  If not, we'll use the pre-generated ones.
if THRIFT is not None:
    class gen_thrift(Command):
        user_options=[]

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            self.mkpath(os.path.join(ROOT, 'sparts', 'gen'))
            for f in glob(os.path.join(ROOT, 'thrift', '*.thrift')):
                self.spawn([THRIFT, '-out', os.path.join(ROOT, 'sparts', 'gen'),
                            '-v', '--gen', 'py:new_style',
                            os.path.join(ROOT, 'thrift', f)])

    cmdclass['gen_thrift'] = gen_thrift


# Custom build_py handler.  Triggers submodule_copy and gen_thrift
# if the environment is right.
class build_py(_build_py):
    def run(self):
        if CAN_COPY:
            self.run_command('submodule_copy')

        if THRIFT is not None:
            self.run_command('gen_thrift')
        _build_py.run(self)

cmdclass['build_py'] = build_py


# Custom PyTest Test command, per https://pytest.org/latest/goodpractises.html
class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['tests', '-rfEsx']
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

cmdclass['test'] = PyTest


class NoDirtyUpload(UploadCommand):
    def run(self):
        result = subprocess.check_output("git status -z", shell=True)
        for fstat in result.split("\x00"):
            stat = fstat[0:2]
            fn = fstat[3:]

            # New files are ok for now.
            if stat == '??':
                continue

            raise AssertionError("Unexpected git status (%s) for %s" %
                (stat, fn))

        UploadCommand.run(self)

cmdclass['upload'] = NoDirtyUpload

install_requires = [
    'six>=1.5',  # 1.5 required for bugfix in six.moves.queue import
    'daemonize',
]
if sys.version < '2.7':
    install_requires.append('ordereddict')

if sys.version < '3.2':
    install_requires.append('futures')

tests_require = install_requires + [
    'pytest',
    'tornado>=1.2',
]

if sys.version < '2.7':
    tests_require.append('unittest2')

if sys.version < '3.3':
    # mock added to 3.3 as unittest.mock
    tests_require.append('mock')

if sys.version < '3.0':
    tests_require.append('Twisted')
    tests_require.append('thrift')
else:
    # Py3k requires Twisted >= 14.0
    tests_require.append('Twisted>=14.0.0')
    # TODO: for py3k use fbthrift instead of thrift?

VERSION = version()
setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(exclude=['tests', 'tests.*']),
    description="Build services in python with as little code as possible",
    long_description=read("README.rst"),

    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'thrift': ['thrift'],
        'tornado': ['tornado'],
        'twisted': ['Twisted'],
    },
    author='Peter Ruibal',
    author_email='ruibalp@gmail.com',
    license='BSD+',
    keywords='service boostrap daemon thrift tornado',
    url='http://github.com/facebook/sparts',
    download_url='https://github.com/facebook/sparts/archive/%s.tar.gz' % VERSION,

    test_suite="tests",
    cmdclass=cmdclass,

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
    ],
)
