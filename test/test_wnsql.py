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
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

########################################################################

import unittest
from yawlib import YLConfig
from yawlib.wordnetsql import WordNetSQL as WSQL

########################################################################


class TestWordNetSQL(unittest.TestCase):

    def get_wn(self):
        # Build a WordNetSQL object (default location: ~/wordnet/sqlite-30.db)
        return WSQL(YLConfig.WNSQL30_PATH)

    def test_wnsql_basic(self):
        wn = self.get_wn()
        self.assertTrue(wn)
        # get sense info
        SID = 300001740
        sinfo = wn.get_senseinfo_by_sid(SID)
        print("Sense info: %s" % (sinfo,))
        examples = wn.get_examples_by_sid(SID)
        print(examples)

    def test_get_freq(self):
        # WSQL should support get_tagcount
        db = self.get_wn()
        c = db.get_tagcount('100002684')
        self.assertEqual(c, 51)

    def test_hypenym_hyponym(self):
        db = self.get_wn()
        sinfo = db.get_senseinfo_by_sk('pleasure%1:09:00::')
        self.assertIsNotNone(sinfo)
        # Hypenyms, hyponyms
        hypehypos = db.get_hypehypo(sinfo.synsetid)
        self.assertEqual(1, len(hypehypos))

########################################################################


def main():
    unittest.main()


if __name__ == "__main__":
    main()
