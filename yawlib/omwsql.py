#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Open Multi-lingual WordNet - SQLite adaptor
'''

# This code is a part of yawlib library: https://github.com/letuananh/yawlib
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import logging
from texttaglib.puchikarui import Schema, with_ctx
from yawlib.models import SynsetID, Synset, SynsetCollection
from yawlib.common import WordnetFeatureNotSupported, InvalidSynsetID


def getLogger():
    return logging.getLogger(__name__)


class OMWNTUMCSchema(Schema):
    def __init__(self, data_source=None, *args, **kwargs):
        Schema.__init__(self, data_source, *args, **kwargs)
        self.add_table('synset', 'synset pos name src'.split(), alias='ss', id_cols=('synset',),)
        self.add_table('word', 'wordid lang lemma pron pos'.split(), alias='word')
        self.add_table('synlink', 'synset1 synset2 link src'.split(), alias='synlink')
        self.add_table('sense', 'synset wordid lang rank lexid freq src'.split(), alias='sense')
        self.add_table('synset_def', 'synset lang def sid usr'.split(), alias='sdef')
        self.add_table('synset_ex', 'synset lang def sid'.split(), alias='sex')


class OMWSQL(OMWNTUMCSchema):
    def __init__(self, db_path, *args, **kwargs):
        super().__init__(db_path, *args, **kwargs)
        self.db_path = db_path

    @with_ctx
    def get_synset(self, synsetid, lang='eng', ctx=None):
        synsetid = self.ensure_sid(synsetid)
        res = ctx.synset.by_id(synsetid)
        synset = Synset(res.synset, lang=lang)
        # select lemma
        words = ctx.word.select('wordid in (SELECT wordid FROM sense WHERE synset=?) and lang=?', (synsetid, lang))
        synset.lemmas.extend((w.lemma for w in words))
        # select defs
        def_rows = ctx.sdef.select("synset=? AND lang=?", (synsetid, lang))
        for row in def_rows:
            synset.definitions.append(row._2)
        # examples
        exes = ctx.sex.select('synset=? and lang=?', (synsetid, lang))
        synset.examples.extend([e._2 for e in exes])
        return synset

    @with_ctx
    def get_synsets(self, synsetids, lang='eng', ctx=None):
        ''' Get synsets by synsetids '''
        synsets = SynsetCollection()
        for sid in synsetids:
            ss = self.get_synset(sid, lang=lang, ctx=ctx)
            synsets.add(ss)
        return synsets

    def ensure_sid(self, synsetid):
        if isinstance(synsetid, SynsetID):
            return synsetid.to_canonical()
        else:
            try:
                return SynsetID.from_string(synsetid).to_canonical()
            except:
                raise InvalidSynsetID(synsetid)

    @with_ctx
    def get_by_key(self, sensekey, lang='eng', ctx=None):
        raise WordnetFeatureNotSupported("This function is not available for this Wordnet")

    @with_ctx
    def get_by_keys(self, sensekeys, lang='eng', ctx=None):
        raise WordnetFeatureNotSupported("This function is not available for this Wordnet")

    @with_ctx
    def sk2sid(self, sensekey, ctx=None):
        raise WordnetFeatureNotSupported("This function is not available for this Wordnet")

    @with_ctx
    def hypernyms(self, synsetid, lang='eng', deep_select=True, ctx=None):
        synsetid = self.ensure_sid(synsetid)
        synsetids = ctx.synlink.select("synset1=? and link='hype'", (synsetid,), columns=('synset2',))
        if deep_select:
            return self.get_synsets(synsetids=(x.synset2 for x in synsetids), lang=lang, ctx=ctx)
        else:
            return [Synset(sid) for sid in synsetids]

    @with_ctx
    def hyponyms(self, synsetid, lang='eng', deep_select=True, ctx=None):
        synsetid = self.ensure_sid(synsetid)
        synsetids = ctx.synlink.select("synset1=? and link='hypo'", (synsetid,), columns=('synset2',))
        if deep_select:
            return self.get_synsets(synsetids=(x.synset2 for x in synsetids), lang=lang, ctx=ctx)
        else:
            return [Synset(sid) for sid in synsetids]

    @with_ctx
    def hypehypo(self, synsetid, lang='eng', deep_select=True, ctx=None):
        synsetid = self.ensure_sid(synsetid)
        synsetids = ctx.synlink.select("synset1=? and link in ('hypo', 'hype')", (synsetid,), columns=('synset2',))
        if deep_select:
            return self.get_synsets(synsetids=(x.synset2 for x in synsetids), lang=lang, ctx=ctx)
        else:
            return [Synset(sid) for sid in synsetids]

    @with_ctx
    def search(self, lemma, pos=None, lang='eng', deep_select=True, ignore_case=True, synsets=None, ctx=None, **kwargs):
        if ignore_case:
            wid_filter = ['lower(lemma) LIKE ?', 'lang=?']
            params = [lemma.lower(), lang]
        else:
            wid_filter = ['lemma LIKE ?', 'lang=?']
            params = [lemma, lang]
        if pos is not None:
            wid_filter.append('pos = ?')
            params.append(pos)
        # ctx is not None
        query = ['wordid in (SELECT wordid FROM word WHERE {})'.format(' AND '.join(wid_filter))]
        query.append('lang=?')
        params.append(lang)
        senses = ctx.sense.select(' AND '.join(query), params, columns=('synset', 'lang',))
        if synsets is None:
            synsets = SynsetCollection()
        for sense in senses:
            if sense.synset not in synsets:
                synsets.add(self.get_synset(sense.synset, lang=sense.lang, ctx=ctx))
        return synsets

    @with_ctx
    def search_def(self, query, deep_select=True, ignore_case=True, lang='eng', synsets=None, ctx=None, **kwargs):
        if ignore_case:
            where = ['lower(def) LIKE ?', 'lang=?']
            params = [query.lower(), lang]
        else:
            where = ['def LIKE ?', 'lang=?']
            params = [query, lang]
        synsetinfos = ctx.sdef.select(' AND '.join(where), params, columns=('synset',))
        if synsets is None:
            synsets = SynsetCollection()
        for sinfo in synsetinfos:
            if sinfo.synset not in synsets:
                synsets.add(self.get_synset(sinfo.synset, lang=lang, ctx=ctx))
        return synsets

    @with_ctx
    def search_ex(self, query, deep_select=True, ignore_case=True, lang='eng', synsets=None, ctx=None, **kwargs):
        if ignore_case:
            where = ['lower(def) LIKE ?', 'lang=?']
            params = [query.lower(), lang]
        else:
            where = ['def LIKE ?', 'lang=?']
            params = [query, lang]
        synsetinfos = ctx.sex.select(' AND '.join(where), params, columns=('synset',))
        if synsets is None:
            synsets = SynsetCollection()
        for sinfo in synsetinfos:
            if sinfo.synset not in synsets:
                synsets.add(self.get_synset(sinfo.synset, lang=lang, ctx=ctx))
        return synsets

    @with_ctx
    def get_synset_def(self, sid_str, lang='eng', ctx=None):
        sid = SynsetID.from_string(sid_str)
        sdef = ctx.sdef.select_single(where='synset=? and lang=?', values=[sid.to_canonical(), lang])
        return sdef._2 if sdef else None
