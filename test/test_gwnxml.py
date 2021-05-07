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
import io
import unittest
import logging
import json

from texttaglib.chirptext import header
from texttaglib.chirptext import texttaglib as ttl
from yawlib.glosswordnet import GWordnetXML

########################################################################

TEST_DIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(TEST_DIR, 'data')
MOCKUP_SYNSETS_DATA = os.path.join(TEST_DATA, 'test.xml')

# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------


def get_logger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# Test cases
# -------------------------------------------------------------------------------

class TestGlossWordNetXML(unittest.TestCase):

    def test_gloss_type(self):
        header("Test read GWN in XML")
        xmlwn = GWordnetXML()
        xmlwn.read(MOCKUP_SYNSETS_DATA)
        # well <00011093-r>
        ss = xmlwn.synsets.by_sid('00011093-r')
        self.assertEqual(len(ss.get_aux()), 2)
        ss.match_surface()
        # note: definition and examples are overrided in GlossedSynset
        expected = {'synsetid': '00011093-r', 'definition': 'in a good or proper or satisfactory manner or to a high standard', 'lemmas': ['well', 'good'], 'sensekeys': ['well%4:02:00::', 'good%4:02:00::'], 'tagcount': 0, 'examples': ['"the children behaved well"', '"a task well done"', '"the party went well"', '"he slept well"', '"a well-argued thesis"', '"a well-seasoned dish"', '"a well-planned party"', '"the baby can walk pretty good"']}
        self.assertEqual(ss.to_json(), expected)
        # containment <03095965-n>
        ss = xmlwn.synsets.by_sid('03095965-n')
        self.assertEqual(len(ss.get_domain()), 1)
        self.assertEqual(ss.get_domain()[0].surface, '(physics)')

    def test_convert_gwnxml_to_json(self):
        header("Test export GWN to JSON")
        xmlwn = GWordnetXML()
        xmlwn.read(MOCKUP_SYNSETS_DATA)
        doc = ttl.Document("glosstest", "~/tmp/doc")
        sc = 0
        synsets = list(xmlwn.synsets)
        for ss in synsets[-50:]:
            for g in ss:
                g.to_ttl(doc)
                sc += 1
        self.assertEqual(len(doc), sc)
        # store json data as text
        output = io.StringIO()
        for sent in doc:
            j = json.dumps(sent.to_json())
            # self.assertTrue(j)
            print(j, file=output)
        jsons = output.getvalue()
        output.close()
        # read them back
        inlines = io.StringIO(jsons)
        for line in inlines:
            j = json.loads(line)
            sent = ttl.Sentence.from_json(j)
            print(sent)

    def validate_data(self):
        header("Test export GWN to JSON")
        xmlwn = GWordnetXML()
        xmlwn.read(MOCKUP_SYNSETS_DATA)
        for ss in xmlwn.synsets:
            idx = 0
            self.assertIsNotNone(ss.get_def())
            self.assertIsNotNone(ss.get_aux())
            try:
                ss.match_surface()
            except Exception as e:
                get_logger().exception("error")
                header(ss.get_surface())
                print(ss.definition)
                if ss.get_aux():
                    print([x.surface for x in ss.get_aux()])
                for e in ss.examples:
                    print(e)
            for g in ss:
                if g.cat == 'aux' or g.cat == 'classif':
                    self.assertIsNone(g.origid)
                elif g.cat == 'def':
                    defid = "{}{}_d".format(ss.ID.pos, ss.ID.offset)
                    self.assertEqual(g.origid, defid)
                    idx += 1
                else:
                    exid = "{}{}_ex{}".format(ss.synsetid.pos, ss.ID.offset, idx)
                    self.assertEqual(g.origid, exid)
                    idx += 1

    def test_extract_xml(self):
        ''' Test data extraction from XML file
        '''
        xmlwn = GWordnetXML()
        xmlwn.read(MOCKUP_SYNSETS_DATA)
        synsets = list(xmlwn.synsets)
        self.assertIsNotNone(synsets)
        self.assertEqual(len(synsets), 219)
        # first synset should be 00001740-r
        ss0 = synsets[0]
        self.assertEqual(ss0.synsetid, '00001740-r')
        self.assertEqual(ss0.lemmas[0], 'a cappella')
        self.assertEqual(ss0.sensekeys[0], 'a_cappella%4:02:00::')
        self.assertEqual(2, len(ss0.glosses))
        tokens = ss0.get_tokens()
        self.assertEqual(tokens, ['a cappella', 'a', 'cappella'])
        # test glosses
        g = ss0.glosses[1]
        self.assertEqual(5, len(g))
        self.assertEqual(g.get_gramwords(), ['they', 'perform', 'a', 'cappella'])
        self.assertEqual(g.text(), 'they performed a cappella;')
        self.assertEqual(ss0.get_surface(), '''without musical accompaniment; "they performed a cappella"''')
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


# -------------------------------------------------------------------------------
# Main method
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
