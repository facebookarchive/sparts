from setuptools import setup, find_packages, Command
from setuptools.command.build_py import build_py as _build_py
from distutils.spawn import find_executable
import os.path
import imp
import pandoc.core


pandoc.core.PANDOC_PATH = find_executable('pandoc')
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
        for f in os.listdir(os.path.join(ROOT, 'thrift')):
            self.spawn(['thrift', '-out', os.path.join(ROOT, 'sparts', 'gen'),
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
    author='Peter Ruibal',
    author_email='ruibalp@gmail.com',
    license='ISC',
    keywords='service boostrap daemon thrift tornado',
    url='http://github.com/fmoo/sparts',

    test_suite="tests",
    cmdclass={'gen_thrift': gen_thrift,
              'build_py': build_py},
)
