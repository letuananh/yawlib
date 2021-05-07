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
__credits__ = ["Le Tuan Anh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

########################################################################

import os
import logging
import unittest
from texttaglib.chirptext import Counter, header
from texttaglib.chirptext.chio import CSV
from texttaglib.chirptext import ttl
from yawlib import YLConfig
from yawlib import WordnetException
from yawlib.glosswordnet import GWordnetXML
from yawlib.glosswordnet import GWordnetSQLite as GWNSQL

########################################################################

logger = logging.getLogger(__name__)
TEST_DIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(TEST_DIR, 'data')
MOCKUP_SYNSETS_DATA = os.path.join(TEST_DATA, 'test.xml')
TEST_DB = os.path.join(TEST_DATA, 'test.db')
TEST_DB_SETUP = os.path.join(TEST_DATA, 'test2.db')

########################################################################


def get_test_gwn(db_path=TEST_DB):
    db = GWNSQL(db_path)
    if not os.path.isfile(db_path) or os.path.getsize(db_path) == 0:
        # insert dummy synsets
        xmlwn = GWordnetXML()
        xmlwn.read(MOCKUP_SYNSETS_DATA)
        db.insert_synsets(xmlwn.synsets)
    return db


def setup_ram_gwn(db, ctx):
    xmlwn = GWordnetXML()
    xmlwn.read(MOCKUP_SYNSETS_DATA)
    db.insert_synsets(xmlwn.synsets, ctx=ctx)


class TestGlossWordnetSQL(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("Setting up tests")

    def test_xml_to_sqlite(self):
        self.assertIsNotNone(get_test_gwn())
        pass

    def test_setup_insert_stuff(self):
        db = GWNSQL(":memory:")
        xmlwn = GWordnetXML()
        xmlwn.read(MOCKUP_SYNSETS_DATA)
        with db.ctx() as ctx:
            synsets = list(xmlwn.synsets)
            db.insert_synset(synsets[0], ctx=ctx)
            db.insert_synsets(synsets[1:3], ctx=ctx)
            # test select stuff out
            ssids = ctx.synset.select()
            self.assertEqual(len(ssids), 3)
            # all tags
            tags = db.tagged_sensekeys(ctx=ctx)
            self.assertEqual(tags, {'not%4:02:00::', 'be_born%2:30:00::', 'christian_era%1:28:00::', 'christ%1:18:00::', 'date%1:28:04::', 'musical_accompaniment%1:10:00::', 'a_cappella%4:02:00::', 'ad%4:02:00::', 'ce%4:02:00::'})
            # all sensekeys
            sks = ctx.sensekey.select()
            self.assertEqual(len(sks), 7)

    def test_results_to_synsets(self):
        db = get_test_gwn()
        db.results_to_synsets([], None)

    def test_get_synset_by_id(self):
        gwn = get_test_gwn()
        ss = gwn.get_synset('00001740-r')
        self.assertIsNotNone(ss)
        self.assertEqual('00001740-r', ss.synsetid)
        self.assertEqual('a cappella', ss.lemmas[0])
        self.assertEqual('a_cappella%4:02:00::', ss.sensekeys[0])
        self.assertEqual(2, len(ss.glosses))
        self.assertEqual('without musical accompaniment;', ss.glosses[0].text())
        self.assertEqual('they performed a cappella;', ss.glosses[1].text())
        pass

    def test_get_synsets_by_ids(self):
        gwn = get_test_gwn()
        synsets = gwn.get_synsets(['00001837-r', 'r00001740'])
        self.assertEqual(len(synsets), 2)
        print(synsets)

    def test_get_gloss_synsets(self):
        print("Test get glossed synset(s)")
        db = get_test_gwn()
        glosses = db.gloss.select()
        # select glosses
        self.assertEqual(len(glosses), 716)
        text = db.get_glossitems_text('00001740r')
        self.assertEqual([x.lemma for x in text], ['without', 'musical%1|musical%3', 'accompaniment%1', '', 'they', 'perform%2', 'a', 'cappella', ''])
        # sensetags
        tags = db.get_sensetags('r00001740')
        self.assertEqual([x.sk for x in tags], ['musical_accompaniment%1:10:00::', 'a_cappella%4:02:00::'])
        pass

    def test_get_synset_by_term(self):
        ss = get_test_gwn().search('AD')
        self.assertGreater(len(ss), 0)

    def test_shallow_search(self):
        gwn = GWNSQL(YLConfig.GWN30_DB)
        ss = gwn.search('dog', deep_select=False)
        self.assertTrue(ss)

    def test_single_match(self):
        gwn = GWNSQL(YLConfig.GWN30_DB)
        ss = gwn.get_synset('r00008007')
        raws = ss.get_orig().split()
        d = ss.get_def()
        for idx, r in enumerate(raws):
            sent = ttl.Sentence(r)
            try:
                tokens = [i.text for i in d.items]
                sent.import_tokens(tokens)
                # found the def raw
                if "(" in r:
                    new_part = r.replace("(", ";(").split(";")
                    raws[idx] = new_part[0]
                    for loc, part in enumerate(new_part[1:]):
                        raws.insert(idx + loc + 1, part)
                    break
            except:
                continue
        print("Before:", ss.get_orig().split())
        print("After:", raws)

    def test_match_surface(self):
        fixed = CSV.read("data/fixed_surface.tab")
        raws_map = {x[0]: x[1:] for x in fixed if x}
        gwn = GWNSQL(YLConfig.GWN30_DB)
        sid = 'v02681795'
        ss = gwn.get_synset(sid)
        raws = raws_map[sid] if sid in raws_map else ss.get_orig().split()
        print("raws: {}".format(raws))
        print("glosses: {}".format([(x.text(), x.cat) for x in ss.glosses]))
        for r, g in zip(raws, ss.glosses):
            tokens = [t.text for t in g]
            while tokens[-1] == ';':
                tokens.pop()
            sent = ttl.Sentence(r)
            sent.import_tokens(tokens)
            print("{} --- {}".format(r, tokens))
        self.assertTrue(ss.match_surface(raws=raws))
        for g in ss.glosses:
            print(g.items, g.surface)

    def test_surface_naive(self):
        fixed = CSV.read("data/fixed_surface.tab")
        raws_map = {x[0]: x[1:] for x in fixed if x}
        to_fix = []
        gwn = get_test_gwn()
        with gwn.ctx() as ctx:
            sinfos = ctx.synset.select(limit=50)
            c = Counter()
            for sinfo in sinfos:
                ss = gwn.get_synset(sinfo.ID, ctx=ctx)
                raws = raws_map[sinfo.ID] if sinfo.ID in raws_map else ss.get_orig().split()
                try:
                    if ss.match_surface(raws=raws):
                        c.count("OK")
                    else:
                        to_fix.append([sinfo.ID] + raws)
                        header("NOT OK - {}".format(sinfo.ID))
                        print("\n".join(raws))
                        print("===")
                        for g in ss.glosses:
                            print("{} ({})".format(g.text(), g.cat))
                        c.count("not OK")
                except:
                    to_fix.append([sinfo.ID] + raws)
                    header("cannot import - {}".format(sinfo.ID))
                    for r, g in zip(raws, ss.glosses):
                        print("{} --- {} ({})".format(r, g.text(), g.cat))
                    c.count("same - wrong import")
            c.summarise()
            CSV.write_tsv("data/manual.txt", to_fix, quoting=CSV.QUOTE_MINIMAL)

    def test_all_api(self):
        gwn = GWNSQL(':memory:')
        with gwn.ctx() as ctx:
            setup_ram_gwn(gwn, ctx)
            self.assertRaises(WordnetException, lambda: gwn.get_synset('00001740-n', ctx=ctx))
            ssids = ctx.synset.select(columns=('ID',))
            self.assertEqual(len(ssids), 219)
            # test get_synset() and get_synsets()
            r00008007 = gwn.get_synset('00008007-r', ctx=ctx)
            self.assertTrue(r00008007)
            self.assertTrue(r00008007.definition)
            self.assertTrue(r00008007.examples)
            self.assertTrue(r00008007.get_aux())
            for ss in gwn.get_synsets(('a01179767', 'n03095965', 'r00001837'), ctx=ctx):
                self.assertTrue(ss.ID)
                self.assertTrue(ss.definition)
                self.assertTrue(ss.keys)
            # test get by key
            r00008007 = gwn.get_by_key('wholly%4:02:00::', ctx=ctx)
            self.assertTrue(r00008007)
            self.assertTrue(r00008007.definition)
            self.assertTrue(r00008007.examples)
            self.assertTrue(r00008007.get_aux())
            # test get_by_keys
            synsets = gwn.get_by_keys(('divine%3:00:02:heavenly:00', 'wholly%4:02:00::'), ctx=ctx)
            for ss in synsets:
                self.assertTrue(ss.definition)
                self.assertTrue(ss.keys)
                self.assertTrue(ss.examples)
            # test sk2sid
            self.assertEqual(gwn.sk2sid('wholly%4:02:00::', ctx=ctx), 'r00008007')
            # test search
            lemma = 'automatically'
            synsets = gwn.search(lemma=lemma, ctx=ctx)
            self.assertTrue(synsets)
            for ss in synsets:
                self.assertTrue(ss.keys)
                self.assertTrue(ss.definition)
                self.assertIn(lemma, ss.lemmas)
            # limit by POS
            self.assertFalse(gwn.search(lemma=lemma, pos='v', ctx=ctx))
            # hypernyms, hyponyms, hypehypo are not supported
            self.assertRaises(WordnetException, lambda: gwn.hypernyms('r00008007', ctx=ctx))
            self.assertRaises(WordnetException, lambda: gwn.hyponyms('r00008007', ctx=ctx))
            self.assertRaises(WordnetException, lambda: gwn.hypehypo('r00008007', ctx=ctx))


########################################################################

if __name__ == "__main__":
    unittest.main()
