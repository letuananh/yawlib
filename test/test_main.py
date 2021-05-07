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
import unittest
import logging
from texttaglib.chirptext.leutile import TextReport
from yawlib import GWordnetXML as GWNXML
from yawlib import GWordnetSQLite as GWNSQL
from yawlib.helpers import get_synset_by_id
from yawlib.helpers import get_synset_by_sk
from yawlib.helpers import get_synsets_by_term
from yawlib.helpers import get_gwn, get_omw
from yawlib.helpers import dump_synset, dump_synsets
from yawlib.helpers import smart_wn_search

from yawlib import YLConfig

########################################################################

TEST_DIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(TEST_DIR, 'data')
MOCKUP_SYNSETS_DATA = os.path.join(TEST_DATA, 'test.xml')


def getLogger():
    return logging.getLogger(__name__)


########################################################################


class TestHelperMethods(unittest.TestCase):

    def test_dump_synset(self):
        print("Test get synset by ID")
        gwn = get_gwn()
        ss = get_synset_by_id(gwn, '01775535-v')
        self.assertIsNotNone(ss)
        self.assertGreater(len(ss.lemmas), 0)
        self.assertGreater(len(ss.sensekeys), 0)
        self.assertGreater(len(ss.glosses), 0)
        rp = TextReport.string()
        dump_synset(ss, report_file=rp)
        getLogger().debug(rp.content())
        pass

    def test_dump_synsets(self):
        dump_synsets(None)

    def test_get_by_term(self):
        with TextReport.null() as rp:
            sses = get_synsets_by_term(GWNSQL(YLConfig.GWN30_DB), 'test', report_file=rp)
            self.assertEqual(len(sses), 13)

    def test_get_by_sk(self):
        with TextReport.null() as rp:
            ss = get_synset_by_sk(get_gwn(), 'test%2:41:00::', report_file=rp)
            self.assertIsNotNone(ss)

    def test_search_wn_full_text(self):
        rp = TextReport.string()
        ss = smart_wn_search(get_omw(), '友達', report_file=rp, lang='jpn')
        sids = {s.ID for s in ss}
        self.assertTrue(ss)
        self.assertEqual(len(sids), len(ss))
        getLogger().debug(rp.content())


class TestGWNXML(unittest.TestCase):

    def test_gwnxml(self):
        xmlwn = GWNXML([MOCKUP_SYNSETS_DATA])
        self.assertEqual(len(xmlwn.synsets), 219)


class TestGlossWordnetSQL(unittest.TestCase):

    def test_synset_info(self):
        xmlwn = GWNXML()
        xmlwn.read(MOCKUP_SYNSETS_DATA)
        synsets = list(xmlwn.synsets)
        ss = synsets[1]
        self.assertIsNotNone(ss)
        self.assertEqual(len(ss.raw_glosses), 2)
        self.assertTrue(ss.raw_glosses[0].gloss)

    def test_get_gloss_synsets(self):
        print("Test get glossed synset(s)")
        db = get_gwn()
        glosses = db.gloss.select()
        # select glosses
        print("Gloss count: {}".format(len(glosses)))
        print(glosses[:5])
        pass


########################################################################

if __name__ == "__main__":
    unittest.main()
