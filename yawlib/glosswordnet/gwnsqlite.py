#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gloss WordNet SQLite Data Access Object - Access Gloss WordNet in SQLite format
"""

# This code is a part of yawlib library: https://github.com/letuananh/yawlib
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
import logging

from texttaglib.puchikarui import Schema, with_ctx, escape_like

from yawlib.models import SynsetCollection, SynsetID, Synset
from yawlib.common import SynsetNotFoundException, WordnetFeatureNotSupported
from yawlib.common import WordnetException

from .gwnmodels import GlossedSynset
from .gwnmodels import GlossItem

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

    @with_ctx
    def insert_synset(self, synset, ctx=None):
        """ Helper method for storing a single synset
        """
        self.insert_synsets([synset], ctx=ctx)

    @with_ctx
    def insert_synsets(self, synsets, ctx=None):
        """ Store synsets with related information (sensekeys, terms, gloss, etc.)
        """
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

    @with_ctx
    def get_synset(self, synsetid, ctx=None, **kwargs):
        ss = GlossedSynset(synsetid)
        synsetid = ss.ID.to_gwnsql()
        if not ctx.synset.by_id(synsetid):
            raise SynsetNotFoundException(synsetid)
        # terms = lemmas;
        terms = ctx.term.select(where='sid=?', values=(synsetid,))
        for term in terms:
            ss.add_lemma(term.term)
        # sensekey;
        sks = ctx.sensekey.select(where='sid=?', values=(synsetid,))
        for sk in sks:
            ss.add_key(sk.sensekey)
        # gloss_raw | sid cat gloss
        rgs = ctx.gloss_raw.select(where='sid=?', values=(synsetid,))
        for rg in rgs:
            ss.add_raw_gloss(rg.cat, rg.gloss)
        # gloss; DB: id origid sid cat | OBJ: gid origid cat
        glosses = ctx.gloss.select(where='sid=?', values=(synsetid,))
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
    def results_to_synsets(self, results, synsets=None, ctx=None, **kwargs):
        if synsets is None:
            synsets = SynsetCollection()
        for result in results:
            ss = self.get_synset(synsetid=result.ID, ctx=ctx, **kwargs)
            synsets.add(ss)
        return synsets

    @with_ctx
    def get_synsets(self, synsetids, ctx=None, **kwargs):
        """ Get synsets by synsetids """
        synsets = SynsetCollection()
        for sid in synsetids:
            ss = self.get_synset(sid, ctx=ctx, **kwargs)
            synsets.add(ss)
        return synsets

    @with_ctx
    def get_by_key(self, sensekey, ctx=None, **kwargs):
        # synset;
        results = ctx.synset.select(where='id IN (SELECT sid FROM sensekey where lower(sensekey)=?)', values=(sensekey.lower(),))
        if len(results) == 0:
            raise SynsetNotFoundException("Could not find any synset with provided key {}".format(sensekey))
        elif len(results) > 1:
            raise WordnetException("Found more than one synsetID with provided key {}".format(sensekey))
        else:
            return self.get_synset(results[0].ID, ctx=ctx)

    @with_ctx
    def get_by_keys(self, sensekeys, ctx=None, **kwargs):
        where = 'id IN (SELECT sid FROM sensekey where lower(sensekey) IN (%s))' % ','.join(['?'] * len(sensekeys))
        results = ctx.synset.select(where=where, values=[k.lower() for k in sensekeys])
        return self.results_to_synsets(results, ctx=ctx, **kwargs)

    @with_ctx
    def sk2sid(self, sensekey, ctx=None):
        result = ctx.sensekey.select_single('sensekey=?', (sensekey,))
        return SynsetID.from_string(result.sid) if result else None

    @with_ctx
    def search(self, lemma, pos=None, deep_select=True, ignore_case=True, synsets=None, ctx=None, **kwargs):
        like_phrase = ' LIKE ? '
        if '%' in lemma or '_' in lemma:
            like_phrase = " LIKE ? ESCAPE '@'"
            lemma = escape_like(lemma)
        if ignore_case:
            query = ['ID IN (SELECT sid FROM term WHERE lower(term) {})'.format(like_phrase)]
            params = [lemma.lower()]
        else:
            query = ['ID IN (SELECT sid FROM term WHERE term {})'.format(like_phrase)]
            params = [lemma]
        if pos:
            query.append('pos = ?')
            params.append(pos)
        # query synsetids
        results = ctx.synset.select(' AND '.join(query), params, columns=('ID',))
        if deep_select:
            return self.results_to_synsets(results, ctx=ctx, synsets=synsets)
        else:
            return SynsetCollection(synsets=(Synset(x.ID) for x in results))

    @with_ctx
    def search_cat(self, query, cat='def', deep_select=True, ignore_case=True, synsets=None, ctx=None, **kwargs):
        if ignore_case:
            where = ['lower(gloss) LIKE ? AND cat=?']
            params = [query.lower(), cat]
        else:
            where = ['gloss LIKE ? AND cat=?']
            params = [query, cat]
        # query synsetids
        results = ctx.gloss_raw.select(' AND '.join(where), params, columns=('sid AS ID',))
        return self.results_to_synsets(results, ctx=ctx, synsets=synsets)

    @with_ctx
    def search_def(self, query, deep_select=True, ignore_case=True, synsets=None, ctx=None, **kwargs):
        return self.search_cat(query, cat='def', deep_select=deep_select, ignore_case=ignore_case, synsets=synsets, ctx=ctx, **kwargs)

    @with_ctx
    def search_ex(self, query, deep_select=True, ignore_case=True, synsets=None, ctx=None, **kwargs):
        return self.search_cat(query, cat='ex', deep_select=deep_select, ignore_case=ignore_case, synsets=synsets, ctx=ctx, **kwargs)

    @with_ctx
    def hypernyms(self, synsetid, deep_select=False, ctx=None):
        raise WordnetFeatureNotSupported("This feature is not available for this Wordnet")

    @with_ctx
    def hyponyms(self, synsetid, deep_select=False, ctx=None):
        raise WordnetFeatureNotSupported("This feature is not available for this Wordnet")

    @with_ctx
    def hypehypo(self, synsetid, deep_select=False, ctx=None):
        raise WordnetFeatureNotSupported("This feature is not available for this Wordnet")

    @with_ctx
    def tagged_sensekeys(self, ctx=None):
        """ Get all sensekeys used for tagging """
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
