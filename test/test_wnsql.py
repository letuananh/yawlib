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

__author__ = "Le Tuan Anh <tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2014, yawlib"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

########################################################################

import os
import logging
import unittest

from yawlib.helpers import get_wn
from texttaglib.chirptext.cli import setup_logging

########################################################################

MY_DIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(MY_DIR, 'data')
wn = get_wn()
setup_logging(os.path.join(MY_DIR, 'logging.json'), os.path.join(MY_DIR, 'logs'))


def getLogger():
    return logging.getLogger(__name__)


class TestWordnetSQL(unittest.TestCase):

    def test_wnsql_basic(self):
        self.assertTrue(wn)
        # get sense info
        SID = 300001740
        ss = wn.get_synset(SID)
        self.assertTrue(ss)
        self.assertTrue(ss.definition)
        self.assertTrue(ss.examples)

    def test_get_synset_by_id(self):
        ss = wn.get_synset('01775164-v')
        self.assertEqual(ss.synsetid, '01775164-v')
        self.assertEqual(ss.definition, 'have a great affection or liking for')
        self.assertEqual(ss.lemmas, ['love'])
        self.assertEqual(ss.lemma, 'love')
        self.assertEqual(ss.sensekeys, ['love%2:37:00::'])
        self.assertEqual(ss.tagcount, 43)
        self.assertEqual(ss.examples, ['I love French food', 'She loves her boss and works hard for him'])

    def test_get_synsets_by_lemma(self):
        synsets = wn.search('love')
        self.assertEqual(len(synsets), 10)
        n07543288 = synsets.by_sid('07543288-n')
        self.assertEqual(n07543288.ID, 107543288)
        self.assertEqual(n07543288.definition, 'a strong positive emotion of regard and affection')
        self.assertEqual(n07543288.tagcount, 42)
        # love, nouns only
        synsets = wn.search('love', pos='n')
        self.assertEqual(set(s.ID for s in synsets), {'13596569-n', '00846515-n', '07488340-n', '09849598-n', '05813229-n', '07543288-n'})
        # search adjective/adverb/etc.
        synsets = wn.search('quick', 'a')
        print(synsets)

    def test_get_satellite(self):
        for s in ['00032733-a', '00919018-a', '00978754-a', '00979366-a', '01270486-a', '01335903-a']:
            self.assertEqual(wn.get_synset(s).ID, s)

    def test_get_by_keys(self):
        with wn.ctx() as ctx:
            ss = wn.get_by_key('love%2:37:00::', ctx=ctx)
            self.assertEqual(ss.synsetid, '01775164-v')
            self.assertEqual(ss.definition, 'have a great affection or liking for')
            self.assertEqual(ss.tagcount, 43)
            synsets = wn.get_by_keys(['canis_familiaris%1:05:00::', 'dog%1:05:00::', 'domestic_dog%1:05:00::'], ctx=ctx)
            self.assertEqual([s.ID for s in synsets], ['02084071-n'])

    def test_get_freq(self):
        # WSQL should support get_tagcount
        c = wn.get_tagcount(100002684)
        self.assertEqual(c, 51)
        c = wn.get_tagcount(100007846)
        self.assertEqual(c, 6909)

    def test_hypenym_hyponym(self):
        sid = wn.sk2sid('pleasure%1:09:00::')
        self.assertIsNotNone(sid)
        # Hypenyms, hyponyms
        hypehypos = wn.hypehypo(sid)
        self.assertEqual(1, len(hypehypos))


########################################################################

if __name__ == "__main__":
    unittest.main()
