#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script for testing yawlib models
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
__credits__ = [ "Le Tuan Anh" ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

########################################################################

import sys
import os
import argparse
import unittest
from chirptext.leutile import FileTool
from yawlib import WordNetSQL as WSQL
from yawlib import XMLGWordNet
from yawlib import SQLiteGWordNet
from yawlib.wntk import combine_glosses
from yawlib import SynsetID, SenseInfo

from yawlib.config import YLConfig
WORDNET_30_PATH = YLConfig.WORDNET_30_PATH
WORDNET_30_GLOSSTAG_PATH = YLConfig.WORDNET_30_GLOSSTAG_PATH
WORDNET_30_GLOSS_DB_PATH = YLConfig.WORDNET_30_GLOSS_DB_PATH
DB_INIT_SCRIPT = YLConfig.DB_INIT_SCRIPT
MOCKUP_SYNSETS_DATA = FileTool.abspath('data/test.xml')
GLOSSTAG_NTUMC_OUTPUT = FileTool.abspath('data/glosstag_ntumc')
GLOSSTAG_PATCH = FileTool.abspath('data/glosstag_patch.xml')
GLOSSTAG_XML_FILES = [os.path.join(YLConfig.WORDNET_30_GLOSSTAG_PATH, 'merged', 'adv.xml'),
                      os.path.join(YLConfig.WORDNET_30_GLOSSTAG_PATH, 'merged', 'adj.xml'),
                      os.path.join(YLConfig.WORDNET_30_GLOSSTAG_PATH, 'merged', 'verb.xml'),
                      os.path.join(YLConfig.WORDNET_30_GLOSSTAG_PATH, 'merged', 'noun.xml')]


########################################################################

class TestSynsetIDWrapper(unittest.TestCase):

    def test_synset_id(self):
        print("Test synset ID")
        sid = SynsetID('12345678', 'n')
        expected_canonical = '12345678-n'
        expected_wnsql = '112345678'
        # validate formats
        self.assertEqual(str(sid), expected_canonical)
        self.assertEqual(sid.to_canonical(), expected_canonical)
        self.assertEqual(sid.to_wnsql(), expected_wnsql)
        # comparing synset
        sid2 = SynsetID.from_string('112345678')
        sid3 = SynsetID.from_string('12345678-n')
        sid4 = SynsetID.from_string('12345678n')
        sid5 = SynsetID.from_string('n12345678')
        sid6 = SynsetID.from_string(112345678)
        self.assertEqual(sid, sid2)
        self.assertEqual(sid, sid3)
        self.assertEqual(sid, sid4)
        self.assertEqual(sid, sid5)
        self.assertEqual(sid, sid6)

    def test_as_dict_key(self):
        s = SynsetID.from_string('12345678n')
        s2 = SynsetID.from_string('112345678')
        d = {}
        d['12345678-n'] = 'abc'
        self.assertEqual(d[s], 'abc')
        self.assertIn(s2, d)

    def test_unusual_sid(self):
        s = SynsetID.from_string('80000683-x')
        self.assertEqual(s.pos, 'x')
        self.assertEqual(s.offset, '80000683')
        # ?
        s = SynsetID.from_string('02315002-a')

    def test_pos(self):
        self.assertEqual(SynsetID.from_string('112345678').pos, 'n')
        self.assertEqual(SynsetID.from_string('212345678').pos, 'v')
        self.assertEqual(SynsetID.from_string('312345678').pos, 'a')
        self.assertEqual(SynsetID.from_string('412345678').pos, 'r')
        self.assertEqual(SynsetID.from_string('512345678').pos, 's')
        self.assertEqual(SynsetID.from_string('n12345678').pos, 'n')
        self.assertEqual(SynsetID.from_string('v12345678').pos, 'v')
        self.assertEqual(SynsetID.from_string('a12345678').pos, 'a')
        self.assertEqual(SynsetID.from_string('r12345678').pos, 'r')
        self.assertEqual(SynsetID.from_string('s12345678').pos, 's')

    def test_synset_wrong_format(self):
        print("Test invalid synset formats")
        self.assertRaises(Exception, lambda: SynsetID.from_string(None))
        # wrong POS (canonical)
        self.assertRaises(Exception, lambda: SynsetID.from_string('12345678g'))
        # wrong POS (WNSQL)
        self.assertRaises(Exception, lambda: SynsetID.from_string('712345678'))
        # wrong POS (WNSQL) #2
        self.assertRaises(Exception, lambda: SynsetID.from_string('k12345678'))
        # no POS
        self.assertRaises(Exception, lambda: SynsetID.from_string('12345678'))

    def test_sense_info(self):
        s = SenseInfo('12345678n', lemma='foo')
        self.assertEqual(s.synsetid, '12345678-n')
        self.assertEqual(s.lemma, 'foo')


######################################################################


def main():
    unittest.main()

if __name__ == "__main__":
    main()
