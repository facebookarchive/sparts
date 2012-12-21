from setuptools import setup, find_packages, Command
from setuptools.command.build_py import build_py as _build_py
from distutils.spawn import find_executable
from glob import glob
import os.path
import imp


def require_binary(name):
    path = find_executable(name)
    assert path is not None, \
        "'%s' is a required binary for building sparts.\n" \
        "Please install it somewhere in your PATH to run this command." \
        % (name)
    return path


pandoc_path = require_binary('pandoc')
import pandoc.core
pandoc.core.PANDOC_PATH = pandoc_path

THRIFT = require_binary('thrift')

ROOT = os.path.abspath(os.path.dirname(__file__))

def read(fname):
    return open(os.path.join(ROOT, fname)).read()

def read_md_as_rest(fname):
    doc = pandoc.Document()
    doc.markdown = read(fname)
    return doc.rst

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

setup(
    name="sparts",
    version=version(),
    packages=find_packages(),
    description="Build services in python with as little code as possible",
    long_description=read_md_as_rest("README.md"),

    install_requires=[],
    setup_requires=['pyandoc', 'unittest2'],
    author='Peter Ruibal',
    author_email='ruibalp@gmail.com',
    license='ISC',
    keywords='service boostrap daemon thrift tornado',
    url='http://github.com/fmoo/sparts',

    test_suite="tests",
    cmdclass={'gen_thrift': gen_thrift,
              'build_py': build_py},

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: ISC License (ISCL)",
    ],
)
