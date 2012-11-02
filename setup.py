from setuptools import setup, find_packages
import os.path
import re
import imp


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def read_md_summary(fname):
    contents = read(fname)
    m = re.match('(.*?)\n[^\n]+\n===', contents,
                 flags=(re.DOTALL | re.MULTILINE))
    if m:
        return m.group(1)
    return contents

def version():
    file, pathname, description = imp.find_module('sparts', ['.'])
    return imp.load_module('sparts', file, pathname, description).__version__

setup(
    name="sparts",
    version=version(),
    packages=find_packages(),
    description="Build services in python with as little code as possible",
    long_description=read_md_summary("README.md"),

    install_requires=[],
    author='Peter Ruibal',
    author_email='ruibalp@gmail.com',
    license='ISC',
    keywords='service boostrap daemon thrift tornado',
    url='http://github.com/fmoo/sparts'
)
