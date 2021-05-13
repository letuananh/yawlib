#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Setup script for YAWLib.

Latest version can be found at https://github.com/letuananh/yawlib

:copyright: (c) 2015 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

# Copyright (c) 2015, Le Tuan Anh <tuananh.ke@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

########################################################################

import io
import os
from setuptools import setup


def read(*filenames, **kwargs):
    ''' Read contents of multiple files and join them together '''
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


# readme_file = 'README.rst' if os.path.isfile('README.rst') else 'README.md'
readme_file = 'README.md'
long_description = read(readme_file)
pkg_info = {}
exec(read('yawlib/__version__.py'), pkg_info)


with open('requirements.txt', 'r') as infile:
    requirements = infile.read().splitlines()


setup(
    name='yawlib',  # package file name (<package-name>-version.tar.gz)
    version=pkg_info['__version__'],
    url=pkg_info['__url__'],
    project_urls={
        "Bug Tracker": "https://github.com/letuananh/yawlib/issues",
        "Source Code": "https://github.com/letuananh/yawlib/"
    },
    keywords=["wordnet", "glosstag", "omw", "sqlite"],
    license=pkg_info['__license__'],
    author=pkg_info['__author__'],
    tests_require=requirements,
    install_requires=requirements,
    author_email=pkg_info['__email__'],
    description=pkg_info['__description__'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['yawlib',
              'yawlib.glosswordnet',
              'yawlib.yawol',
              'yawlib.yawol.django',
              'yawlib.yawol.django.migrations'],
    package_data={'yawlib': ['data/*.json',
                             'glosswordnet/script/*.sql']},
    include_package_data=True,
    platforms='any',
    test_suite='test',
    # Reference: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=['Programming Language :: Python',
                 'Development Status :: {}'.format(pkg_info['__status__']),
                 'Natural Language :: English',
                 'Environment :: Plugins',
                 'Intended Audience :: Developers',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: {}'.format(pkg_info['__license__']),
                 'Operating System :: OS Independent',
                 'Topic :: Text Processing',
                 'Topic :: Text Processing :: Linguistic',
                 'Topic :: Software Development :: Libraries :: Python Modules']
)
