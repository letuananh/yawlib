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
import argparse
import unittest
from chirptext.leutile import FileTool
from yawlib.wordnetsql import WordNetSQL as WSQL
from yawlib.glosswordnet import XMLGWordNet
from yawlib.glosswordnet import SQLiteGWordNet as GWNSQL
from yawlib.glosswordnet import Gloss
from yawlib.helpers import get_synset_by_id
from yawlib.helpers import get_synset_by_sk
from yawlib.helpers import get_synsets_by_term
from yawlib.helpers import dump_synset, dump_synsets
from yawlib.wntk import combine_glosses

from yawlib.config import YLConfig
WORDNET_30_PATH          = YLConfig.WORDNET_30_PATH
WORDNET_30_GLOSSTAG_PATH = YLConfig.WORDNET_30_GLOSSTAG_PATH
WORDNET_30_GLOSS_DB_PATH = YLConfig.WORDNET_30_GLOSS_DB_PATH
DB_INIT_SCRIPT           = YLConfig.DB_INIT_SCRIPT
MOCKUP_SYNSETS_DATA      = FileTool.abspath('data/test.xml')
GLOSSTAG_NTUMC_OUTPUT    = FileTool.abspath('data/glosstag_ntumc')
GLOSSTAG_PATCH           = FileTool.abspath('data/glosstag_patch.xml')
GLOSSTAG_XML_FILES = [
    os.path.join(YLConfig.WORDNET_30_GLOSSTAG_PATH , 'merged', 'adv.xml')
    ,os.path.join(YLConfig.WORDNET_30_GLOSSTAG_PATH, 'merged', 'adj.xml')
    ,os.path.join(YLConfig.WORDNET_30_GLOSSTAG_PATH, 'merged', 'verb.xml')
    ,os.path.join(YLConfig.WORDNET_30_GLOSSTAG_PATH, 'merged', 'noun.xml')
    ]


########################################################################


def get_gwn():
    return GWNSQL(YLConfig.WORDNET_30_GLOSS_DB_PATH)


class TestGlossWordNetSQL(unittest.TestCase):

    def test_get_synset_by_id(self):
        gwn = get_gwn()
        ss = gwn.get_synset_by_id('00001740-r')
        self.assertIsNotNone(ss)
        self.assertEqual('00001740-r', ss.sid)
        self.assertEqual('a cappella', ss.terms[0].term)
        self.assertEqual('a_cappella%4:02:00::', ss.keys[0].sensekey)
        self.assertEqual(2, len(ss.glosses))
        self.assertEqual('without musical accompaniment;', ss.glosses[0].text())
        self.assertEqual('they performed a cappella;', ss.glosses[1].text())
        pass

    def test_get_synsets_by_ids(self):
        gwn = get_gwn()
        synsets = gwn.get_synsets_by_ids(['01828736-v', '00001740-r'])
        self.assertEqual(len(synsets), 2)
        print(synsets)

    def test_get_gloss_synsets(self):
        print("Test get glossed synset(s)")
        db = get_gwn()
        glosses = db.schema.gloss.select()
        # select glosses
        print("Gloss count: {}".format(len(glosses)))
        print(glosses[:5])
        # select glossitems
        # gitems = db.schema.glossitem.select(columns='id ord gid lemma'.split())
        # print("Glossitem count: {}".format(len(gitems)))
        # print(gitems[:5])
        # fetch all synsets
        # ss = db.all_synsets()
        # print("Synsets: {}".format(len(ss)))
        # print(ss[:5])
        pass

########################################################################


def main():
    unittest.main()


if __name__ == "__main__":
    main()
