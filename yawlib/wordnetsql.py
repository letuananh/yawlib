#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WordNet SQLite wrapper
"""

# This code is a part of yawlib library: https://github.com/letuananh/yawlib
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import logging
from collections import defaultdict as dd
from texttaglib.puchikarui import Schema, with_ctx
from yawlib.models import SynsetID, Synset, SynsetCollection


def getLogger():
    return logging.getLogger(__name__)


class Wordnet3Schema(Schema):

    """SQLite schema for WordnetSQL (Princeton WordNet version 3.0)"""
    def __init__(self, data_source=None):
        Schema.__init__(self, data_source)
        self.add_table('wordsXsensesXsynsets', 'wordid lemma casedwordid synsetid senseid sensenum lexid tagcount sensekey pos lexdomainid definition'.split(), alias='wss')
        self.add_table('wordsXsenses', 'wordid lemma casedwordid synsetid senseid sensenum lexid tagcount sensekey'.split(), alias='wordsense')
        self.add_table('sensesXsemlinksXsenses', 'linkid ssynsetid swordid ssenseid scasedwordid ssensenum slexid stagcount ssensekey spos slexdomainid sdefinition dsynsetid dwordid dsenseid dcasedwordid dsensenum dlexid dtagcount dsensekey dpos dlexdomainid ddefinition'.split(), alias='sss')
        self.add_table('synsets', 'synsetid pos lexdomainid definition'.split(), alias='ss').set_id('synsetid')
        self.add_table('samples', 'synsetid sampleid sample'.split(), alias='ex')
        self.add_table('senses', 'wordid casedwordid synsetid senseid sensenum lexid tagcount sensekey'.split())
        self.add_table('semlinks', 'synset1id synset2id linkid'.split())


class WordnetSQL(Wordnet3Schema):

    def __init__(self, db_path, **kwargs):
        super().__init__(data_source=db_path, **kwargs)
        # Caches
        self.sk_cache = dd(set)
        self.sid_cache = dd(set)
        self.hypehypo_cache = dd(set)
        self.tagcount_cache = dd(lambda: 0)

    def ensure_sid(self, sid):
        """Ensure that a given synset ID is an instance of SynsetID"""
        if isinstance(sid, SynsetID):
            sid = sid.to_wnsql()
        else:
            sid = SynsetID.from_string(str(sid)).to_wnsql()
        return sid

    @with_ctx
    def get_synset(self, synsetid, ctx=None, **kwargs):
        sid = self.ensure_sid(synsetid)
        # get synset object
        synset_info = ctx.ss.by_id(sid)
        if synset_info is None:
            return None
        else:
            ss = Synset(synset_info.synsetid)
            ss.definition = synset_info.definition
            # add lemmas, sensekeys and tag count
            rows = ctx.wordsense.select('synsetid=?', (sid,), columns=('lemma', 'sensekey', 'tagcount'))
            for row in rows:
                ss.add_lemma(row.lemma)
                ss.add_key(row.sensekey)
                ss.tagcount += row.tagcount
            # add examples
            exes = ctx.ex.select(where='synsetid=?', values=[sid], orderby='sampleid')
            for ex in exes:
                ss.examples.append(ex.sample)
            return ss

    @with_ctx
    def get_synsets(self, synsetids, ctx=None, **kwargs):
        """ Get synsets by synsetids """
        synsets = SynsetCollection()
        for sid in synsetids:
            ss = self.get_synset(sid, ctx=ctx)
            synsets.add(ss)
        return synsets

    @with_ctx
    def sk2sid(self, sensekey, ctx=None):
        return ctx.select_scalar('select synsetid from senses where lower(sensekey)=?', (sensekey,))

    @with_ctx
    def get_by_key(self, sensekey, ctx=None, **kwargs):
        # get synset object
        sid = self.sk2sid(sensekey.lower(), ctx=ctx)
        return self.get_synset(sid, ctx=ctx)

    @with_ctx
    def get_by_keys(self, sensekeys, ctx=None, **kwargs):
        query = 'lower(sensekey) IN ({})'.format(', '.join(len(sensekeys) * ['?']))
        results = ctx.senses.select(query, [s.lower() for s in sensekeys], columns=('synsetid',))
        # get synset object
        return self.get_synsets(set(s.synsetid for s in results), ctx=ctx)

    def get_synsets_by_lemma(self, lemma):
        with self.schema.ds.open() as ctx:
            # get synset object
            rows = ctx.wss.select(where='lemma=?', values=(lemma,))
            synsets = SynsetCollection()
            if rows is not None and len(rows) > 0:
                for row in rows:
                    ss = Synset(row.synsetid)
                    ss.definition = row.definition
                    ss.add_lemma(row.lemma)
                    ss.add_key(row.sensekey)
                    ss.tagcount = row.tagcount
                    # add examples
                    exes = ctx.ex.select(where='synsetid=?', values=[row.synsetid], orderby='sampleid')
                    for ex in exes:
                        ss.examples.append(ex.sample)
                    synsets.add(ss)
            return synsets

    @with_ctx
    def search(self, lemma, pos=None, deep_select=True, synsets=None, ignore_case=True, ctx=None, **kwargs):
        # Build query
        if ignore_case:
            query = ['wordid IN (SELECT wordid FROM words WHERE lower(lemma) LIKE ?)']
            params = [lemma.lower()]
        else:
            query = ['wordid IN (SELECT wordid FROM words WHERE lemma LIKE ?)']
            params = [lemma]
        if pos == 'a':
            # ss_type: https://wordnet.princeton.edu/man/wndb.5WN.html
            # n    NOUN
            # v    VERB
            # a    ADJECTIVE
            # s    ADJECTIVE SATELLITE
            # r    ADVERB
            query.append("synsetid IN (SELECT synsetid FROM synsets WHERE pos IN ('a', 's'))")
        elif pos:
            query.append('synsetid IN (SELECT synsetid FROM synsets WHERE pos = ?)')
            params.append(pos)
        # find synsetIDs first
        senses = ctx.senses.select(' AND '.join(query), params, columns=('synsetid',))
        # get synset object
        synsets = SynsetCollection()
        if senses:
            for sense in senses:
                ss = self.get_synset(sense.synsetid, ctx=ctx)
                synsets.add(ss)
        return synsets

    @with_ctx
    def hypehypo(self, sid, ctx=None):
        """ Get all hypernyms and hyponyms of a given synset
        """
        sid = SynsetID.from_string(str(sid))
        if sid in self.hypehypo_cache:
            return self.hypehypo_cache[sid]
        result = ctx.semlinks.select(
            where='synset1id = ? and linkid in (1,2,3,4,11,12,13,14,15,16,40,50,81)',
            values=[sid.to_wnsql()])
        for r in result:
            self.hypehypo_cache[sid].add(r.synset2id)
        return self.hypehypo_cache[sid]

    @with_ctx
    def get_tagcount(self, sid, ctx=None, **kwargs):
        sid = self.ensure_sid(sid)
        return ctx.select_scalar('SELECT SUM(tagcount) FROM senses WHERE synsetid=?', (sid,))
