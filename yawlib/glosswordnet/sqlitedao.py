#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Gloss WordNet SQLite Data Access Object - Access Gloss WordNet in SQLite format
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

#-----------------------------------------------------------------------

import os
import logging

from puchikarui import Schema, with_ctx

from yawlib.models import SynsetCollection, Synset, SynsetID

from .models import GlossedSynset
from .models import GlossItem

# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

SETUP_SCRIPT = os.path.join(os.path.dirname(__file__), 'script', 'gwn_setup.sql')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# -------------------------------------------------------------------------------
# Schema
# -------------------------------------------------------------------------------

class GWordnetSchema(Schema):
    def __init__(self, data_source=None, setup_file=SETUP_SCRIPT):
        Schema.__init__(self, data_source, setup_file=SETUP_SCRIPT)
        self.add_table('meta', 'title license WNVer url maintainer'.split())
        self.add_table('synset', 'ID offset pos'.split()).set_id('ID')
        # --
        self.add_table('term', 'sid term'.split())
        self.add_table('gloss_raw', 'sid cat gloss'.split())
        self.add_table('sensekey', 'sid sensekey'.split())
        # --
        self.add_table('gloss', 'id origid sid cat surface'.split())
        self.add_table('glossitem', 'id ord gid tag lemma pos cat coll rdf sep text origid'.split())
        self.add_table('sensetag', 'id cat tag glob glob_lemma glob_id coll sid gid sk origid lemma itemid'.split())


# -------------------------------------------------------------------------------
# Features
# -------------------------------------------------------------------------------

class GWordnetSQLite(GWordnetSchema):

    def __init__(self, db_path, **kwargs):
        super().__init__(data_source=db_path, **kwargs)
        # self.db_path = db_path
        # self.schema = GWordnetSchema(self.db_path)

    @property
    def schema(self):
        return self

    @with_ctx
    def insert_synset(self, synset, ctx=None):
        ''' Helper method for storing a single synset
        '''
        self.insert_synsets([synset])

    @with_ctx
    def insert_synsets(self, synsets, ctx=None):
        ''' Store synsets with related information (sensekeys, terms, gloss, etc.)
        '''
        # synset;
        for synset in synsets:
            sid = synset.ID.to_gwnsql()
            ctx.synset.insert(sid, synset.ID.offset, synset.ID.pos)
            # term;
            for term in synset.lemmas:
                ctx.term.insert(sid, term)
            # sensekey;
            for sk in synset.sensekeys:
                ctx.sensekey.insert(sid, sk)
            # gloss_raw;
            for gloss_raw in synset.raw_glosses:
                ctx.gloss_raw.insert(sid, gloss_raw.cat, gloss_raw.gloss)
            # gloss; DB: id origid sid cat | OBJ: gid origid cat
            for gloss in synset.glosses:
                gloss.gid = ctx.gloss.insert(gloss.origid, sid, gloss.cat, gloss.surface)
                # glossitem;
                # OBJ | gloss, order, tag, lemma, pos, cat, coll, rdf, origid, sep, text
                # DB  | id ord gid tag lemma pos cat coll rdf sep text origid
                for item in gloss.items:
                    item.itemid = ctx.glossitem.insert(item.order, gloss.gid, item.tag, item.lemma, item.pos, item.cat, item.coll, item.rdf, item.sep, item.text, item.origid)
                # sensetag;
                for tag in gloss.tags:
                    # OBJ: tagid cat, tag, glob, glemma, gid, coll, origid, sid, sk, lemma
                    # DB: id cat tag glob glob_lemma glob_id coll sid gid sk origid lemma itemid
                    ctx.sensetag.insert(tag.cat, tag.tag, tag.glob, tag.glemma,
                                        tag.glob_id, tag.coll, '', gloss.gid, tag.sk,
                                        tag.origid, tag.lemma, tag.item.itemid)
        pass

    @with_ctx
    def get_synset(self, sid, ctx=None):
        ss = GlossedSynset(sid)
        sid = ss.ID.to_gwnsql()
        # terms = lemmas;
        terms = ctx.term.select(where='sid=?', values=(sid,))
        for term in terms:
            ss.add_lemma(term.term)
        # sensekey;
        sks = ctx.sensekey.select(where='sid=?', values=(sid,))
        for sk in sks:
            ss.add_key(sk.sensekey)
        # gloss_raw | sid cat gloss
        rgs = ctx.gloss_raw.select(where='sid=?', values=(sid,))
        for rg in rgs:
            ss.add_raw_gloss(rg.cat, rg.gloss)
        # gloss; DB: id origid sid cat | OBJ: gid origid cat
        glosses = ctx.gloss.select(where='sid=?', values=(sid,))
        for gl in glosses:
            gloss = ss.add_gloss(gl.origid, gl.cat, gl.id)
            gloss.surface = gl.surface
            # glossitem;
            # OBJ | gloss, order, tag, lemma, pos, cat, coll, rdf, origid, sep, text
            # DB  | id ord gid tag lemma pos cat coll rdf sep text origid
            glossitems = ctx.glossitem.select(where='gid=?', values=(gl.id,))
            item_map = {}
            for gi in glossitems:
                item = gloss.add_gloss_item(gi.tag, gi.lemma, gi.pos, gi.cat, gi.coll, gi.rdf, gi.origid, gi.sep, gi.text, gi.id)
                item_map[item.itemid] = item
            # sensetag;
            # OBJ: tagid cat, tag, glob, glemma, gid, coll, origid, sid, sk, lemma
            # DB: id cat tag glob glob_lemma glob_id coll sid gid sk origid lemma itemid
            tags = ctx.sensetag.select(where='gid=?', values=(gl.id,))
            for tag in tags:
                gloss.tag_item(item_map[tag.itemid], tag.cat, tag.tag, tag.glob, tag.glob_lemma,
                               tag.glob_id, tag.coll, tag.origid, tag.sid, tag.sk, tag.lemma, tag.id)
        return ss

    @with_ctx
    def results_to_synsets(self, results, synsets=None, ctx=None):
        if synsets is None:
            synsets = SynsetCollection()
        for result in results:
            ss = self.get_synset(sid=result.ID, ctx=ctx)
            synsets.add(ss)
        return synsets

    @with_ctx
    def get_synsets_by_ids(self, synsetids, ctx=None):
        synsets = SynsetCollection()
        for sid in synsetids:
            ss = self.get_synset(sid, ctx=ctx)
            synsets.add(ss)
        return synsets

    @with_ctx
    def all_synsets(self, synsets=None, deep_select=True, ctx=None):
        synsets = SynsetCollection()
        results = ctx.synset.select()
        if deep_select:
            return self.results_to_synsets(results, ctx=ctx, synsets=synsets)
        else:
            for result in results:
                synsets.add(Synset(result.ID))
            return synsets

    @with_ctx
    def get_synset_by_sk(self, sensekey, ctx=None):
        # synset;
        results = ctx.synset.select(where='id IN (SELECT sid FROM sensekey where sensekey=?)', values=(sensekey,))
        if len(results) == 0:
            raise Exception("Could not find any synset with provided key {}".format(sensekey))
        elif len(results) > 1:
            raise Exception("Found more than one synsetID with provided key {}".format(sensekey))
        else:
            return self.get_synset(results[0].ID, ctx=ctx)

    @with_ctx
    def get_synset_by_sks(self, sensekeys, ctx=None):
        where = 'id IN (SELECT sid FROM sensekey where sensekey IN (%s))' % ','.join(['?'] * len(sensekeys))
        results = ctx.synset.select(where=where, values=sensekeys)
        return self.results_to_synsets(results, ctx=ctx)

    @with_ctx
    def get_synsets_by_lemma(self, lemma, ctx=None):
        rows = ctx.term.select('lower(term)=?', (lemma.lower(),))
        synsets = SynsetCollection()
        for row in rows:
            synsets.add(self.get_synset(row.sid, ctx=ctx))
        return synsets

    @with_ctx
    def search(self, lemma, pos=None, deep_select=True, synsets=None, ignore_case=True, ctx=None):
        if ignore_case:
            query = ['ID IN (SELECT sid FROM term WHERE lower(term) LIKE ?)']
            params = [lemma.lower()]
        else:
            query = ['ID IN (SELECT sid FROM term WHERE term LIKE ?)']
            params = [lemma]
        if pos:
            query.append('pos = ?')
            params.append(pos)
        # query synsetids
        results = ctx.synset.select(' AND '.join(query), params)
        return self.results_to_synsets(results, ctx=ctx, synsets=synsets)

    @with_ctx
    def sensekeys(self, ctx=None):
        return ctx.sensekey.select()

    @with_ctx
    def tagged_sensekeys(self, ctx=None):
        results = ctx.sensetag.select(columns=['sk'])
        return set((x.sk for x in results))

    @with_ctx
    def get_glossitems_text(self, synsetid, ctx=None):
        sid = SynsetID.from_string(synsetid).to_gwnsql()
        where = 'gid IN (SELECT id FROM gloss WHERE sid = ?)'
        results = ctx.glossitem.select(where=where, values=[sid],
                                       columns=['id', 'lemma', 'pos', 'text'])
        items = []
        for item in results:
            g = GlossItem(gloss=None, tag=None, lemma=item.lemma, pos=item.pos, cat=None,
                          coll=None, rdf=None, origid=None, sep=None, text=None, itemid=item.id)
            items.append(g)
        return items

    @with_ctx
    def get_sensetags(self, synsetid, ctx=None):
        sid = SynsetID.from_string(synsetid).to_gwnsql()
        return ctx.sensetag.select(where='gid IN (SELECT id FROM gloss WHERE sid = ?)',
                                   values=[sid],
                                   columns=['id', 'lemma', 'sk'])
