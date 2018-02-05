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

import unittest
import logging
from yawlib.helpers import get_omw
from yawlib.common import WordnetFeatureNotSupported
from yawlib.helpers import dump_synset

########################################################################

omw = get_omw()


def getLogger():
    return logging.getLogger(__name__)


########################################################################

class TestOMWSQL(unittest.TestCase):

    def test_get_synset_def(self):
        with omw.ctx() as ctx:
            ssdef = omw.get_synset_def('05797597-n', lang='eng', ctx=ctx)
            self.assertEqual(ssdef, 'a search for knowledge')
            ssdef = omw.get_synset_def('05797597-n', lang='jpn', ctx=ctx)
            self.assertEqual(ssdef, '知識を得るための調査')

    def test_get_synset(self):
        sid = '05797597-n'
        with omw.ctx() as ctx:
            ss = omw.get_synset(sid, ctx=ctx)
            self.assertEqual(ss.synsetid, sid)
            self.assertEqual(ss.lemmas, ['inquiry', 'enquiry', 'research'])
            self.assertEqual(ss.definitions, ['a search for knowledge'])
            self.assertEqual(ss.examples, ['their pottery deserves more research than it has received'])
            # Japanese WordNet
            ss = omw.get_synset(sid, lang='jpn')
            self.assertEqual(ss.synsetid, sid)
            self.assertEqual(ss.lemmas, ['リサーチ', '問い合わせ', '質問', '調査', '照会'])
            self.assertEqual(ss.definitions, ['知識を得るための調査'])
            self.assertEqual(ss.examples, ['彼らの陶器製造法には、今よりもずっと多くの問い合わせがあってもいい'])

    def test_search(self):
        word = 'research'
        synsets = omw.search(word)
        sids = {s.synsetid.to_canonical() for s in synsets}
        self.assertEqual(sids, {'00877327-v', '00636921-n', '05797597-n', '00648224-v'})
        self.assertEqual(synsets.by_sid('00648224-v').to_json(), {"examples": ["the students had to research the history of the Second World War for their history project", "He searched for information on his relatives on the web", "Scientists are exploring the nature of consciousness"], "definition": "inquire into", "sensekeys": [], "lemmas": ["explore", "research", "search"], "tagcount": 0, "synsetid": "00648224-v"})
        # search with pos
        synsets = omw.search(word, 'n')
        sids = {s.synsetid.to_canonical() for s in synsets}
        self.assertEqual(sids, {'00636921-n', '05797597-n'})
        # Japanese lemmas
        synsets = omw.search("研究", lang="jpn")
        defs = {s.definition for s in synsets}
        sids = {s.synsetid.to_canonical() for s in synsets}
        expected = {'本質的な特徴か意味を発見するために、詳細に検討し分析する', '事実を立証するための系統的な調査', '体系的および科学的に調査することを試みる', '熱心な調査と思考', '演奏者のある一面を伸ばすための曲', '勉学をする; 履修要項にしたがう; 学校に登録する'}
        self.assertEqual(defs, expected)
        self.assertEqual(sids, {'00607405-v', '00636921-n', '07048627-n', '00644583-v', '00877327-v', '05784242-n'})

    def test_search_def_and_ex(self):
        with omw.ctx() as ctx:
            ss = omw.search_def('%友達%', lang='jpn', ctx=ctx)
            for s in ss:
                self.assertTrue('友達' in s.definition)
            ss = omw.search_ex('%友達%', lang='jpn', ctx=ctx)
            for s in ss:
                self.assertTrue('友達' in ''.join(s.examples))

    def test_all_api(self):
        with omw.ctx() as ctx:
            # test get_synset() and get_synsets()
            r00008007 = omw.get_synset('00008007-r', ctx=ctx)
            self.assertTrue(r00008007)
            self.assertTrue(r00008007.definition)
            self.assertTrue(r00008007.examples)
            for ss in omw.get_synsets(('a01179767', 'n03095965', 'r00001837'), ctx=ctx):
                self.assertTrue(ss.ID)
                self.assertTrue(ss.definition)
                # self.assertTrue(ss.keys)
            # test get by key(s)
            self.assertRaises(WordnetFeatureNotSupported, lambda: omw.get_by_key('wholly%4:02:00::', lang='eng', ctx=ctx))
            self.assertRaises(WordnetFeatureNotSupported, lambda: omw.get_by_keys(['wholly%4:02:00::'], lang='eng', ctx=ctx))
            # test sk2sid
            self.assertRaises(WordnetFeatureNotSupported, lambda: omw.sk2sid('wholly%4:02:00::', ctx=ctx))
            # test search
            lemma = 'automatically'
            synsets = omw.search(lemma=lemma, ctx=ctx)
            self.assertTrue(synsets)
            for ss in synsets:
                self.assertTrue(ss.definition)
                self.assertIn(lemma, ss.lemmas)
            # limit by POS
            self.assertFalse(omw.search(lemma=lemma, pos='v', ctx=ctx))
            # hypernyms, hyponyms, hypehypo are not supported
            n02084071 = omw.get_synset('02084071-n', ctx=ctx)
            hypers = omw.hypernyms(n02084071.ID, ctx=ctx)
            expected_hypers = {'01317541-n', '02083346-n'}
            self.assertEqual(set(x.ID for x in hypers), expected_hypers)
            hypos = omw.hyponyms(n02084071.ID, ctx=ctx)
            expected_hypos = {'01322604-n', '02111500-n', '02110806-n', '02111277-n', '02085272-n', '02113335-n', '02111129-n', '02085374-n', '02111626-n', '02084732-n', '02084861-n', '02113978-n', '02087122-n', '02103406-n', '02110341-n', '02110958-n', '02112826-n', '02112497-n', '90000574-n'}
            self.assertEqual(set(x.ID for x in hypos), expected_hypos)
            # test search def and ex
            synsets = omw.search_def('%superman%', ctx=ctx)
            for s in synsets:
                self.assertIn('superman', s.definition)
            synsets = omw.search_ex('%superman%', ctx=ctx)
            for s in synsets:
                self.assertIn('superman', ' ||| '.join(s.examples).lower())


########################################################################


if __name__ == "__main__":
    unittest.main()
