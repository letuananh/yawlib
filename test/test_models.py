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

import unittest
import logging
from yawlib import POS, SynsetID, Synset, SynsetCollection
from yawlib import WordnetException
from yawlib.glosswordnet import GlossedSynset, GlossGroup, GlossRaw

########################################################################

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
        s = SynsetID.from_string(s)
        self.assertEqual(s.pos, 'x')
        self.assertEqual(s.offset, '80000683')
        # ?
        s = SynsetID.from_string('02315002-a')

    def test_pos(self):
        self.assertEqual(POS.num2pos(1), 'n')
        self.assertEqual(POS.num2pos("1"), 'n')
        self.assertRaises(WordnetException, lambda: POS.num2pos("7"))
        self.assertRaises(WordnetException, lambda: POS.num2pos(None))
        self.assertRaises(WordnetException, lambda: POS.num2pos(0))
        self.assertEqual(POS.pos2num("n"), '1')
        self.assertEqual(POS.pos2num("v"), '2')
        self.assertEqual(POS.pos2num("a"), '3')
        self.assertEqual(POS.pos2num("r"), '4')
        self.assertEqual(POS.pos2num("s"), '5')
        self.assertEqual(POS.pos2num("x"), '6')
        self.assertRaises(WordnetException, lambda: POS.pos2num(None))
        self.assertRaises(WordnetException, lambda: POS.pos2num("g"))
        self.assertRaises(WordnetException, lambda: POS.pos2num(""))
        self.assertRaises(WordnetException, lambda: POS.pos2num(1))
        self.assertRaises(WordnetException, lambda: POS.pos2num("n "))
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

    def test_synset(self):
        s = Synset('12345678n', lemma='foo')
        ss = SynsetCollection()
        ss.add(s)
        self.assertEqual(s.synsetid, '12345678-n')
        self.assertEqual(s.lemma, 'foo')

    def test_collection(self):
        s = Synset('12345678n', lemma='foo')
        ss = SynsetCollection()
        ss.add(s)
        self.assertIn(112345678, ss)
        self.assertIs(ss[112345678], s)
        self.assertEqual(len(ss), 1)

    def test_assign_synsetid(self):
        s1 = SynsetID.from_string('12345678-n')
        ss = Synset(s1)
        ssid = ss.ID
        self.assertIs(ss.ID, ssid)
        self.assertEqual(ss.ID, s1)
        self.assertIsNot(ss.ID, s1)  # must not be the same instance SynsetID


class testGSynset(unittest.TestCase):

    def test_gsynset(self):
        gs = GlossedSynset(112345678)
        self.assertIsNotNone(gs)
        self.assertEqual(str(gs), '(GSynset:12345678-n)')
        # def should be none now
        self.assertIsNone(gs.get_def())
        self.assertIsNone(gs.definition)
        # add an empty gloss item
        gs.add_raw_gloss('boo', 'boo foo')
        g = gs.add_gloss(None, None)
        g.add_gloss_item(*([None] * 7))
        words = gs[0].get_gramwords()
        self.assertEqual(words, [])
        # now a valid gloss item
        g.add_gloss_item('', 'foo%1|boo%2', '', '', '', '', '')
        words = g.get_gramwords()
        self.assertEqual(set(words), {'boo', 'foo'})
        self.assertEqual(gs.get_surface(), '')
        # gloss group
        self.assertIsNotNone(GlossGroup())

    def test_glossraw(self):
        g = GlossRaw(None, GlossRaw.ORIG, 'without musical accompaniment; "they performed a cappella"')
        self.assertEqual(str(g), '[gloss-orig] without musical accompaniment; "they performed a cappella"')
        self.assertEqual(g.split(), ['without musical accompaniment', ' "they performed a cappella"'])


######################################################################

if __name__ == "__main__":
    unittest.main()
