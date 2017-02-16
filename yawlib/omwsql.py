#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Open Multi-lingual WordNet - SQLite adaptor
Latest version can be found at https://github.com/letuananh/yawlib

@author: Le Tuan Anh <tuananh.ke@gmail.com>
'''

# Copyright (c) 2017, Le Tuan Anh <tuananh.ke@gmail.com>
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
__copyright__ = "Copyright 2017, yawlib"
__credits__ = [ "Le Tuan Anh" ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

#-----------------------------------------------------------------------

from puchikarui import Schema, Execution
from yawlib.models import SynsetID

#-----------------------------------------------------------------------


class OMWNTUMCSchema(Schema):
    def __init__(self, data_source=None):
        Schema.__init__(self, data_source)
        self.add_table('synset', 'synset pos name src'.split(), alias='ss')
        self.add_table('word', 'wordid lang lemma pron pos'.split(), alias='word')
        self.add_table('synlink', 'synset1 synset2 link src'.split(), alias='synlink')
        self.add_table('sense', 'synset wordid lang rank lexid freq src'.split(), alias='sense')
        self.add_table('synset_def', 'synset lang def sid'.split(), alias='sdef')
        self.add_table('synset_ex', 'synset lang def sid'.split(), alias='sex')


class OMWSQL:
    def __init__(self, db_path):
        self.db_path = db_path
        self.schema = OMWNTUMCSchema(self.db_path)
        # some cache here?

    def get_all_synsets(self):
        with Execution(self.schema) as exe:
            return exe.schema.ss.select()

    def get_synset_def(self, sid_str, lang='eng'):
        sid = SynsetID.from_string(sid_str)
        with Execution(self.schema) as exe:
            defs = exe.schema.sdef.select(where='synset=? and lang=?', values=[sid.to_canonical(), lang])
            assert len(defs) in (0, 1)
            if defs:
                return defs[0]._2
