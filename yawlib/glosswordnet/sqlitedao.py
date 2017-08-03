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

from puchikarui import Schema

from yawlib.models import SynsetCollection, SynsetID

from .models import GlossedSynset
from .models import GlossItem

#-----------------------------------------------------------------------

SETUP_SCRIPT = os.path.join(os.path.dirname(__file__), 'script', 'gwn_setup.sql')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class GWordnetSchema(Schema):
    def __init__(self, data_source=None, setup_file=SETUP_SCRIPT):
        Schema.__init__(self, data_source, setup_file=SETUP_SCRIPT)
        self.add_table('meta', 'title license WNVer url maintainer'.split())
        self.add_table('synset', 'id offset pos'.split())
        # --
        self.add_table('term', 'sid term'.split())
        self.add_table('gloss_raw', 'sid cat gloss'.split())
        self.add_table('sensekey', 'sid sensekey'.split())
        # --
        self.add_table('gloss', 'id origid sid cat'.split())
        self.add_table('glossitem', 'id ord gid tag lemma pos cat coll rdf sep text origid'.split())
        self.add_table('sensetag', 'id cat tag glob glob_lemma glob_id coll sid gid sk origid lemma itemid'.split())

# -----------------------------------------------------------------------


class GWordnetSQLite:
    def __init__(self, db_path, verbose=False):
        self.db_path = db_path
        self.schema = GWordnetSchema(self.db_path)
        if verbose:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)

    def insert_synset(self, synset):
        ''' Helper method for storing a single synset
        '''
        self.insert_synsets([synset])

    def insert_synsets(self, synsets):
        ''' Store synsets with related information (sensekeys, terms, gloss, etc.)
        '''
        with self.schema.ds.open() as ctx:
            # synset;
            for synset in synsets:
                sid = synset.sid.to_gwnsql()
                ctx.synset.insert(sid, synset.sid.offset, synset.sid.pos)
                # term;
                for term in synset.lemmas:
                    ctx.term.insert(sid, term)
                # sensekey;
                for sk in synset.keys:
                    ctx.sensekey.insert(sid, sk)
                # gloss_raw;
                for gloss_raw in synset.raw_glosses:
                    ctx.gloss_raw.insert(sid, gloss_raw.cat, gloss_raw.gloss)
                # gloss; DB: id origid sid cat | OBJ: gid origid cat
                for gloss in synset.glosses:
                    gloss.gid = ctx.gloss.insert(gloss.origid, sid, gloss.cat)
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

    def results_to_synsets(self, results, ctx, synsets=None):
        if synsets is None:
            synsets = SynsetCollection()
        for result in results:
            ss = GlossedSynset(result.id)
            sid = ss.sid.to_gwnsql()
            # term;
            terms = ctx.term.select(where='sid=?', values=[sid])
            for term in terms:
                ss.add_lemma(term.term)
            # sensekey;
            sks = self.schema.sensekey.select(where='sid=?', values=[sid], ctx=ctx)
            for sk in sks:
                ss.add_key(sk.sensekey)
            # gloss_raw | sid cat gloss
            rgs = self.schema.gloss_raw.select(where='sid=?', values=[sid], ctx=ctx)
            for rg in rgs:
                ss.add_raw_gloss(rg.cat, rg.gloss)
            # gloss; DB: id origid sid cat | OBJ: gid origid cat
            glosses = self.schema.gloss.select(where='sid=?', values=[sid], ctx=ctx)
            for gl in glosses:
                gloss = ss.add_gloss(gl.origid, gl.cat, gl.id)
                # glossitem;
                # OBJ | gloss, order, tag, lemma, pos, cat, coll, rdf, origid, sep, text
                # DB  | id ord gid tag lemma pos cat coll rdf sep text origid
                glossitems = self.schema.glossitem.select(where='gid=?', values=[gl.id], ctx=ctx)
                item_map = {}
                for gi in glossitems:
                    item = gloss.add_gloss_item(gi.tag, gi.lemma, gi.pos, gi.cat, gi.coll, gi.rdf, gi.origid, gi.sep, gi.text, gi.id)
                    item_map[item.itemid] = item
                # sensetag;
                # OBJ: tagid cat, tag, glob, glemma, gid, coll, origid, sid, sk, lemma
                # DB: id cat tag glob glob_lemma glob_id coll sid gid sk origid lemma itemid
                tags = self.schema.sensetag.select(where='gid=?', values=[gl.id], ctx=ctx)
                for tag in tags:
                    gloss.tag_item(item_map[tag.itemid], tag.cat, tag.tag, tag.glob, tag.glob_lemma,
                                   tag.glob_id, tag.coll, tag.origid, tag.sid, tag.sk, tag.lemma, tag.id)
            synsets.add(ss)
        return synsets

    def get_synset_by_id(self, synsetid):
        # ensure that synsetid is an instance of SynsetID
        sid = SynsetID.from_string(synsetid)
        with self.schema.ds.open() as exe:
            results = self.schema.synset.select(where='id=?', values=[sid.to_gwnsql()])
            if results:
                synsets = self.results_to_synsets(results, exe)
                if len(synsets) == 1:
                    return synsets[0]
                else:
                    logger.warning("Multiple synsets retrieved for sid={}".format(synsetid))
        return None

    def get_synsets_by_ids(self, synsetids):
        sids = [str(SynsetID.from_string(x).to_gwnsql()) for x in synsetids]
        synsets = SynsetCollection()
        with self.schema.ds.open() as ctx:
            # synset;
            wherecon = 'id IN (%s)' % (','.join(['?'] * len(sids)))
            results = ctx.synset.select(where=wherecon, values=sids)
            if results:
                return self.results_to_synsets(results, ctx, synsets)
        return synsets

    def all_synsets(self, synsets=None, deep_select=True):
        synsets = SynsetCollection()
        with self.schema.ds.open() as ctx:
            # synset;
            results = self.schema.synset.select(ctx=ctx)
            if results:
                if deep_select:
                    return self.results_to_synsets(results, ctx, synsets)
                else:
                    return results
        return synsets

    def get_synset_by_sk(self, sensekey):
        with self.schema.ds.open() as ctx:
            # synset;
            results = ctx.synset.select(where='id IN (SELECT sid FROM sensekey where sensekey=?)', values=[sensekey])
            if results:
                synsets = self.results_to_synsets(results, ctx)
                if synsets and len(synsets) == 1:
                    return synsets[0]
        raise Exception("Could not find any synset with provided key {}".format(sensekey))

    def get_synset_by_sks(self, sensekeys):
        synsets = SynsetCollection()
        with self.schema.ds.open() as ctx:
            # synset;
            where = 'id IN (SELECT sid FROM sensekey where sensekey IN (%s))' % ','.join(['?'] * len(sensekeys))
            results = ctx.synset.select(where=where, values=sensekeys)
            if results:
                return self.results_to_synsets(results, ctx, synsets)
        return synsets

    def get_synsets_by_term(self, term, pos=None, synsets=None, sid_only=False):
        synsets = SynsetCollection()
        with self.schema.ds.open() as ctx:
            # synset;
            if pos:
                results = ctx.synset.select(where='pos = ? AND id IN (SELECT sid FROM term where lower(term)=?)', values=[pos, term.lower()])
            else:
                results = ctx.synset.select(where='id IN (SELECT sid FROM term where lower(term)=?)', values=[term.lower()])
            if results:
                if sid_only:
                    return results
                else:
                    return self.results_to_synsets(results, ctx, synsets)
        return synsets

    def get_all_sensekeys(self):
        return self.schema.sensekey.select()

    def get_all_sensekeys_tagged(self):
        results = self.schema.sensetag.select(columns=['sk'])
        sensekeys = set()
        for result in results:
            sensekeys.add(result.sk)
        return sensekeys

    def get_glossitems_text(self, synsetid):
        sid = SynsetID.from_string(synsetid).to_gwnsql()
        where = 'gid IN (SELECT id FROM gloss WHERE sid = ?)'
        results = self.schema.glossitem.select(where=where, values=[sid],
                                               columns=['id', 'lemma', 'pos', 'text'])
        items = []
        for item in results:
            g = GlossItem(gloss=None, tag=None, lemma=item.lemma, pos=item.pos, cat=None,
                          coll=None, rdf=None, origid=None, sep=None, text=None, itemid=item.id)
            items.append(g)
        return items

    def get_sensetags(self, synsetid):
        sid = SynsetID.from_string(synsetid).to_gwnsql()
        return self.schema.sensetag.select(where='gid IN (SELECT id FROM gloss WHERE sid = ?)',
                                           values=[sid],
                                           columns=['id', 'lemma', 'sk'])
