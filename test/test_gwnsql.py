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
from yawlib.glosswordnet import GWordnetXML
from yawlib.glosswordnet import GWordnetSQLite as GWNSQL

########################################################################

TEST_DIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(TEST_DIR, 'data')
MOCKUP_SYNSETS_DATA = os.path.join(TEST_DATA, 'test.xml')
TEST_DB = os.path.join(TEST_DATA, 'test.db')

########################################################################


def get_gwn(db_path=TEST_DB):
    db = GWNSQL(db_path)
    if not os.path.isfile(db_path) or os.path.getsize(TEST_DB) == 0:
        db.setup()
        # insert dummy synsets
        xmlwn = GWordnetXML()
        xmlwn.read(MOCKUP_SYNSETS_DATA)
        db.insert_synsets(xmlwn.synsets)
    return db


class TestGlossWordNetSQL(unittest.TestCase):

    def test_xml_to_sqlite(self):
        self.assertIsNotNone(get_gwn())
        pass

    def test_get_synset_by_id(self):
        gwn = get_gwn()
        ss = gwn.get_synset_by_id('00001740-r')
        self.assertIsNotNone(ss)
        self.assertEqual('00001740-r', ss.sid)
        self.assertEqual('a cappella', ss.lemmas[0])
        self.assertEqual('a_cappella%4:02:00::', ss.keys[0])
        self.assertEqual(2, len(ss.glosses))
        self.assertEqual('without musical accompaniment;', ss.glosses[0].text())
        self.assertEqual('they performed a cappella;', ss.glosses[1].text())
        pass

    def test_get_synsets_by_ids(self):
        gwn = get_gwn()
        synsets = gwn.get_synsets_by_ids(['00001837-r', 'r00001740'])
        self.assertEqual(len(synsets), 2)
        print(synsets)

    def test_get_gloss_synsets(self):
        print("Test get glossed synset(s)")
        db = get_gwn()
        glosses = db.schema.gloss.select()
        # select glosses
        print("Gloss count: {}".format(len(glosses)))
        print(glosses[:5])
        pass

    def test_get_synset_by_term(self):
        ss = get_gwn().get_synsets_by_term('AD')
        self.assertGreater(len(ss), 0)

########################################################################


def main():
    unittest.main()


if __name__ == "__main__":
    main()
