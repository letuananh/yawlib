#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script for testing yawlib library
Latest version can be found at https://github.com/letuananh/yawlib

Adapted from: https://github.com/letuananh/lelesk

@author: Le Tuan Anh <tuananh.ke@gmail.com>
'''

# Copyright (c) 2016, Le Tuan Anh <tuananh.ke@gmail.com>
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

__author__ = "Le Tuan Anh <tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2014, yawlib"
__credits__ = ["Le Tuan Anh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

########################################################################

import os
import unittest
import logging
from yawlib.glosswordnet import GWordnetXML

########################################################################

TEST_DIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(TEST_DIR, 'data')
MOCKUP_SYNSETS_DATA = os.path.join(TEST_DATA, 'test.xml')

########################################################################

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class TestGlossWordNetXML(unittest.TestCase):

    def test_extract_xml(self):
        ''' Test data extraction from XML file
        '''
        xmlwn = GWordnetXML()
        xmlwn.read(MOCKUP_SYNSETS_DATA)
        synsets = xmlwn.synsets
        self.assertIsNotNone(synsets)
        self.assertEqual(len(synsets), 218)
        # first synset should be 00001740-r
        ss0 = synsets[0]
        self.assertEqual('00001740-r', ss0.sid)
        self.assertEqual('a cappella', ss0.lemmas[0])
        self.assertEqual('a_cappella%4:02:00::', ss0.keys[0])
        self.assertEqual(2, len(ss0.glosses))
        # test glosses
        g = ss0.glosses[1]
        self.assertEqual(5, len(g))
        self.assertEqual(g.get_gramwords(), ['they', 'perform', 'a', 'cappella'])
        self.assertEqual(g.text(), 'they performed a cappella;')
        # gloss item
        self.assertEqual(g[1].get_lemma(), 'performed')
        self.assertEqual(g[1].get_gramwords(), {'perform'})
        # sense tag
        self.assertEqual(g.tags[0].lemma, 'a cappella')
        self.assertEqual(g.tags[0].sk, 'a_cappella%4:02:00::')

########################################################################


def main():
    unittest.main()


if __name__ == "__main__":
    main()
