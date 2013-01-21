from setuptools import setup, find_packages, Command
from setuptools.command.build_py import build_py as _build_py
from distutils.spawn import find_executable
from glob import glob
import os.path
import imp


THRIFT = find_executable('thrift')

ROOT = os.path.abspath(os.path.dirname(__file__))

def read(fname):
    """Read a file relative to the repository root"""
    return open(os.path.join(ROOT, fname)).read()

def exists(fname):
    """Returns True if `fname` relative to `ROOT` exists"""
    return os.path.exists(os.path.join(ROOT, fname))

def version():
    """Return the version number from sparts/__version__.py"""
    file, pathname, description = imp.find_module('sparts', [ROOT])
    return imp.load_module('sparts', file, pathname, description).__version__

# Initialize custom command handlers
cmdclass = {}

# These files are shadowed in the source repository from
# externals.  If you are developing sparts, you can use git submodule to make
# sure you have the latest/greatest fb303 from thrift.
WANT_COPY = {
    'externals/thrift/contrib/fb303/if/fb303.thrift':
        'thrift/fb303.thrift', 
    'externals/thrift/contrib/fb303/py/fb303/FacebookBase.py':
        'sparts/fb303/FacebookBase.py', 
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

VERSION = version()
setup(
    name="sparts",
    version=VERSION,
    packages=find_packages(),
    description="Build services in python with as little code as possible",
    long_description=read("README.rst"),

    install_requires=[],
    setup_requires=['unittest2'],
    author='Peter Ruibal',
    author_email='ruibalp@gmail.com',
    license='ISC',
    keywords='service boostrap daemon thrift tornado',
    url='http://github.com/fmoo/sparts',
    download_url='https://github.com/fmoo/sparts/archive/%s.tar.gz' % VERSION,

    test_suite="tests",
    cmdclass=cmdclass,

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: ISC License (ISCL)",
    ],
)
