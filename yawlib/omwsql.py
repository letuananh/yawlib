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
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

# -----------------------------------------------------------------------

from puchikarui import Schema
from yawlib.models import SynsetID, Synset, SynsetCollection


# -----------------------------------------------------------------------

class OMWNTUMCSchema(Schema):
    def __init__(self, data_source=None, *args, **kwargs):
        Schema.__init__(self, data_source, *args, **kwargs)
        self.add_table('synset', 'synset pos name src'.split(), alias='ss', id_cols=('synset',),)
        self.add_table('word', 'wordid lang lemma pron pos'.split(), alias='word')
        self.add_table('synlink', 'synset1 synset2 link src'.split(), alias='synlink')
        self.add_table('sense', 'synset wordid lang rank lexid freq src'.split(), alias='sense')
        self.add_table('synset_def', 'synset lang def sid'.split(), alias='sdef')
        self.add_table('synset_ex', 'synset lang def sid'.split(), alias='sex')


class OMWSQL(OMWNTUMCSchema):
    def __init__(self, db_path, *args, **kwargs):
        super().__init__(db_path, *args, **kwargs)
        self.db_path = db_path

    def get_all_synsets(self, ctx=None):
        if ctx is None:
            with self.ctx() as ctx:
                return self.get_all_synsets(ctx=ctx)
        return ctx.ss.select()

    def get_synset(self, sid_str, lang='eng', ctx=None):
        if ctx is None:
            with self.ctx() as ctx:
                return self.get_synset(sid_str, lang=lang, ctx=ctx)
        # ctx is not None
        sid = SynsetID.from_string(sid_str)
        res = ctx.synset.by_id(sid.to_canonical())
        synset = Synset(res.synset)
        # select lemma
        words = ctx.word.select('wordid in (SELECT wordid FROM sense WHERE synset=?) and lang=?', (sid.to_canonical(), lang))
        synset.lemmas.extend((w.lemma for w in words))
        # select defs
        def_rows = ctx.sdef.select("synset=? AND lang=?", (sid.to_canonical(), lang))
        for row in def_rows:
            synset.definitions.append(row._2)
        # examples
        exes = ctx.sex.select('synset=? and lang=?', (sid.to_canonical(), lang))
        synset.examples.extend([e._2 for e in exes])
        return synset

    def search(self, lemma, pos=None, lang='eng', ctx=None):
        if ctx is None:
            with self.ctx() as ctx:
                return self.search(lemma, pos=pos, lang=lang, ctx=ctx)
        wid_filter = ['lemma LIKE ?', 'lang=?']
        params = [lemma, lang]
        if pos is not None:
            wid_filter.append('pos = ?')
            params.append(pos)
        # ctx is not None
        query = ['wordid in (SELECT wordid FROM word WHERE {})'.format(' AND '.join(wid_filter))]
        query.append('lang=?')
        params.append(lang)
        senses = ctx.sense.select(' AND '.join(query), params)
        synsets = SynsetCollection()
        for sense in senses:
            synsets.add(self.get_synset(sense.synset, lang=sense.lang, ctx=ctx))
        return synsets

    def get_synset_def(self, sid_str, lang='eng', ctx=None):
        if ctx is None:
            with self.ctx() as ctx:
                return self.get_synset_def(sid_str, lang, ctx=ctx)
        sid = SynsetID.from_string(sid_str)
        sdef = ctx.sdef.select_single(where='synset=? and lang=?', values=[sid.to_canonical(), lang])
        return sdef._2 if sdef else None
