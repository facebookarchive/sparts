from setuptools import setup, find_packages
import os.path
import re

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def read_md_summary(fname):
    contents = read(fname)
    m = re.match('(.*?)\n[^\n]+\n===', contents,
                 flags=(re.DOTALL | re.MULTILINE))
    if m:
        return m.group(1)
    return contents

setup(
    name="sparts",
    version="0.1",
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
