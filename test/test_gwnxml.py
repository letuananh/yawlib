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
        self.assertEqual(ss0.sid, '00001740-r')
        self.assertEqual(ss0.lemmas[0], 'a cappella')
        self.assertEqual(ss0.keys[0], 'a_cappella%4:02:00::')
        self.assertEqual(2, len(ss0.glosses))
        tokens = ss0.get_tokens()
        self.assertEqual(tokens, ['a cappella', 'a', 'cappella'])
        # test glosses
        g = ss0.glosses[1]
        self.assertEqual(5, len(g))
        self.assertEqual(g.get_gramwords(), ['they', 'perform', 'a', 'cappella'])
        self.assertEqual(g.text(), 'they performed a cappella;')
        self.assertEqual(ss0.get_orig_gloss(), '''without musical accompaniment; "they performed a cappella"''')
        self.assertEqual(ss0.get_gramwords(), ['without', 'musical', 'accompaniment', 'they', 'perform', 'a', 'cappella'])
        # get_tags() returns a list of tagged sense keys
        self.assertEqual(ss0.get_tags(), ['musical_accompaniment%1:10:00::', 'a_cappella%4:02:00::'])
        # gloss item
        self.assertEqual(g[1].get_lemma(), 'performed')
        self.assertEqual(g[1].get_gramwords(), {'perform'})
        # sense tag
        self.assertEqual(g.tags[0].lemma, 'a cappella')
        self.assertEqual(g.tags[0].sk, 'a_cappella%4:02:00::')
        self.assertEqual(g.get_tagged_sensekey(), ['a_cappella%4:02:00::'])
        # str and repr
        self.assertEqual(str(g), "{Gloss('r00001740_ex1'|'ex') they performed a cappella;}")
        self.assertEqual(repr(g), "gloss-ex")
        # glossitem
        self.assertEqual(str(g[0]), "(itemid: r00001740_wf5 | id:r00001740_wf5 | tag:ignore | lemma:they | pos: | cat: | coll: | rdf:  | sep: | text:they)")
        self.assertEqual(repr(g[0]), "'they'")
        # tags
        self.assertEqual(str(g.tags[0]), "a cappella (sk:a_cappella%4:02:00:: | itemid: coll:b | cat:cf | tag:auto | glob:auto | glemma:a_cappella%3|a_cappella%4 | gid:r00001740_coll.b | coll:b | origid: r00001740_id.2)")
        self.assertEqual(repr(g.tags[0]), "a cappella (sk:a_cappella%4:02:00::)")

########################################################################


def main():
    unittest.main()


if __name__ == "__main__":
    main()
