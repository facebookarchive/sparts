from setuptools import setup, find_packages, Command
from setuptools.command.build_py import build_py as _build_py
from distutils.spawn import find_executable
from glob import glob
import os.path
import imp


THRIFT = find_executable('thrift')

ROOT = os.path.abspath(os.path.dirname(__file__))

def read(fname):
    return open(os.path.join(ROOT, fname)).read()

def version():
    file, pathname, description = imp.find_module('sparts', [ROOT])
    return imp.load_module('sparts', file, pathname, description).__version__

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

class build_py(_build_py):
    def run(self):
        self.run_command('gen_thrift')
        _build_py.run(self)


cmdclass = {}
# If we have a thrift compiler installed, let's use it to re-generate
# the .py files.  If not, we'll use the pre-generated ones.
if THRIFT is not None:
    cmdclass = {'gen_thrift': gen_thrift,
                'build_py': build_py}

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
