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

import sys
import os
import unittest
from yawlib.omwsql import OMWSQL
from yawlib.config import YLConfig

########################################################################


class TestOMWSQL(unittest.TestCase):

    def get_wn(self):
        # Build a OMWSQL object (default location: ~/wordnet/wn-ntumc.db)
        return OMWSQL(YLConfig.OMW_DB)

    def test_wnsql_basic(self):
        wn = self.get_wn()
        self.assertTrue(wn)
        # get all available synsets
        ss = wn.get_all_synsets()
        self.assertGreater(len(ss), 120000)
        self.assertEqual(ss[0].synset, "00001740-a")

    def test_get_synset_def(self):
        wn = self.get_wn()
        ssdef = wn.get_synset_def('05797597-n')
        self.assertEqual(ssdef, 'a search for knowledge')

    def test_get_synset(self):
        wn = self.get_wn()
        sid = '05797597-n'
        # Princeton WordNet (by default)
        ss = wn.get_synset(sid)
        self.assertEqual(ss.synsetid, sid)
        self.assertEqual(ss.lemmas, ['inquiry', 'enquiry', 'research'])
        self.assertEqual(ss.defs, ['a search for knowledge'])
        self.assertEqual(ss.exes, ['their pottery deserves more research than it has received'])
        # Japanese WordNet
        ss = wn.get_synset(sid, lang='jpn')
        self.assertEqual(ss.synsetid, sid)
        self.assertEqual(ss.lemmas, ['リサーチ', '問い合わせ', '質問', '調査', '照会'])
        self.assertEqual(ss.defs, ['知識を得るための調査'])
        self.assertEqual(ss.exes, ['彼らの陶器製造法には、今よりもずっと多くの問い合わせがあってもいい'])

    def test_search(self):
        word = 'research'
        wn = self.get_wn()
        synsets = wn.search(word)
        sids = {s.synsetid.to_canonical() for s in synsets}
        self.assertEqual(sids, {'00877327-v', '00636921-n', '05797597-n', '00648224-v'})
        self.assertEqual(synsets.by_sid('00648224-v').to_json(), {"examples": ["the students had to research the history of the Second World War for their history project", "He searched for information on his relatives on the web", "Scientists are exploring the nature of consciousness"], "definition": "inquire into", "sensekeys": [], "lemmas": ["explore", "research", "search"], "tagcount": 0, "synsetid": "00648224-v"})

########################################################################


if __name__ == "__main__":
    unittest.main()
