# -*- coding: utf-8 -*-

''' Test scripts for YAWLib
Latest version can be found at https://github.com/letuananh/yawlib

References:
    Python documentation:
        https://docs.python.org/
    Python unittest
        https://docs.python.org/3/library/unittest.html
    --
    PEP 257 - Python Docstring Conventions:
        https://www.python.org/dev/peps/pep-0257/

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT
'''

# This source code is a part of YAWLib
# Copyright (c) 2015, Le Tuan Anh <tuananh.ke@gmail.com>
# LICENSE: The MIT License (MIT)
#
# Homepage: https://github.com/letuananh/yawlib

import os
from texttaglib.chirptext.cli import setup_logging


TEST_DIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(TEST_DIR, 'data')
setup_logging(os.path.join(TEST_DIR, 'logging.json'), os.path.join(TEST_DIR, 'logs'))


__all__ = ['TEST_DIR', 'TEST_DATA']
