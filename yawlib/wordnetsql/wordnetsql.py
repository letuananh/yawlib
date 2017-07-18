#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
WordNet SQLite wrapper
Latest version can be found at https://github.com/letuananh/lelesk

@author: Le Tuan Anh <tuananh.ke@gmail.com>
'''

# Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>
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
__copyright__ = "Copyright 2014, lelesk"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

#-----------------------------------------------------------------------

import sqlite3
from collections import defaultdict as dd
from puchikarui import Schema
from yawlib.config import YLConfig
from yawlib.models import SynsetID, Synset, SynsetCollection

#-----------------------------------------------------------------------


class Wordnet3Schema(Schema):

    '''SQLite schema for WordnetSQL (Princeton WordNet version 3.0)'''
    def __init__(self, data_source=None):
        Schema.__init__(self, data_source)
        self.add_table('wordsXsensesXsynsets', 'wordid lemma casedwordid synsetid senseid sensenum lexid tagcount sensekey pos lexdomainid definition'.split(), alias='wss')
        self.add_table('sensesXsemlinksXsenses', 'linkid ssynsetid swordid ssenseid scasedwordid ssensenum slexid stagcount ssensekey spos slexdomainid sdefinition dsynsetid dwordid dsenseid dcasedwordid dsensenum dlexid dtagcount dsensekey dpos dlexdomainid ddefinition'.split(), alias='sss')
        self.add_table('synsets', 'synsetid pos definition'.split(), alias='ss')
        self.add_table('samples', 'synsetid sampleid sample'.split(), alias='ex')


class WordnetSQL:

    def __init__(self, db_path):
        self.db_path = db_path
        self.schema = Wordnet3Schema(self.db_path)
        # Caches
        self.sk_cache = dd(set)
        self.sid_cache = dd(set)
        self.hypehypo_cache = dd(set)
        self.tagcount_cache = dd(lambda: 0)

    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        return conn

    def get_all_synsets(self):
        return self.schema.wss.select(columns=['synsetid', 'lemma', 'sensekey', 'tagcount'])

    def get_synset_by_id(self, synsetid):
        sid = self.ensure_sid(synsetid)
        with self.schema.ds.open() as exe:
            # get synset object
            rows = self.schema.wss.select(where='synsetid=?', values=(sid,), exe=exe)
            if rows is not None and len(rows) > 0:
                ss = Synset(synsetid)
                ss.definition = rows[0].definition
                for row in rows:
                    ss.add_lemma(row.lemma)
                    ss.add_key(row.sensekey)
                    ss.tagcount += row.tagcount
                # add examples
                exes = self.schema.ex.select(where='synsetid=?', values=[sid], orderby='sampleid', exe=exe)
                for ex in exes:
                    ss.exes.append(ex.sample)
                return ss

    def get_synset_by_sk(self, sk):
        with self.schema.ds.open() as exe:
            # get synset object
            rows = self.schema.wss.select(where='sensekey=?', values=(sk,), exe=exe)
            if rows is not None and len(rows) > 0:
                ss = Synset(rows[0].synsetid)
                ss.definition = rows[0].definition
                for row in rows:
                    ss.add_lemma(row.lemma)
                    ss.add_key(row.sensekey)
                    ss.tagcount += row.tagcount
                # add examples
                exes = self.schema.ex.select(where='synsetid=?', values=[rows[0].synsetid], orderby='sampleid', exe=exe)
                for ex in exes:
                    ss.exes.append(ex.sample)
                return ss

    def get_synsets_by_lemma(self, lemma):
        with self.schema.ds.open() as exe:
            # get synset object
            rows = self.schema.wss.select(where='lemma=?', values=(lemma,), exe=exe)
            synsets = SynsetCollection()
            if rows is not None and len(rows) > 0:
                for row in rows:
                    ss = Synset(row.synsetid)
                    ss.definition = row.definition
                    ss.add_lemma(row.lemma)
                    ss.add_key(row.sensekey)
                    ss.tagcount = row.tagcount
                    # add examples
                    exes = self.schema.ex.select(where='synsetid=?', values=[row.synsetid], orderby='sampleid', exe=exe)
                    for ex in exes:
                        ss.exes.append(ex.sample)
                    synsets.add(ss)
            return synsets

    def cache_tagcounts(self):
        results = self.schema.wss.select(columns=['synsetid', 'tagcount'])
        for res in results:
            self.tagcount_cache[res.synsetid] += res.tagcount

    def get_tagcount(self, sid):
        if sid in self.tagcount_cache:
            return self.tagcount_cache[sid]
        results = self.schema.wss.select(where='synsetid=?', values=[sid], columns=['tagcount'])
        counter = 0
        for res in results:
            counter += res.tagcount
        self.tagcount_cache[sid] = counter
        return counter

    def get_senseinfo_by_sk(self, sk):
        if sk in self.sk_cache:
            return self.sk_cache[sk]
        result = self.schema.wss.select_single(where='sensekey=?', values=[sk],
                                               columns=['pos', 'synsetid', 'sensekey'])
        self.sk_cache[sk] = result
        return result

    def ensure_sid(self, sid):
        '''Ensure that a given synset ID is an instance of SynsetID'''
        if isinstance(sid, SynsetID):
            sid = sid.to_wnsql()
        else:
            sid = SynsetID.from_string(str(sid)).to_wnsql()
        return sid

    def get_senseinfo_by_sid(self, synsetid):
        sid = self.ensure_sid(synsetid)
        if sid in self.sid_cache:
            return self.sid_cache[sid]
        result = self.schema.wss.select_single(where='synsetid=?', values=[sid],
                                                  columns=['pos', 'synsetid',
                                                           'sensekey', 'definition', 'tagcount'])
        self.sid_cache[sid] = result
        return result

    def get_examples_by_sid(self, synsetid):
        sid = self.ensure_sid(synsetid)
        result = self.schema.ex.select(where='synsetid=?', values=[sid], orderby='sampleid')
        return result

    def get_all_sensekeys(self):
        results = self.schema.wss.select(columns=['pos', 'synsetid', 'sensekey'])
        return results

    def cache_all_sensekey(self):
        results = self.schema.wss.select(columns=['pos', 'synsetid', 'sensekey'])
        for result in results:
            self.sk_cache[result.sensekey] = result

    def get_hypehypo(self, sid):
        ''' Get all hypernyms and hyponyms of a given synset
        '''
        sid = SynsetID.from_string(str(sid))
        if sid in self.hypehypo_cache:
            return self.hypehypo_cache[sid]
        result = self.schema.sss.select(where='ssynsetid = ? and linkid in (1,2,3,4, 11,12,13,14,15,16,40,50,81)',
                                        values=[sid.to_wnsql()],
                                        columns=['linkid', 'dpos', 'dsynsetid', 'dsensekey', 'dwordid'])
        for r in result:
            self.hypehypo_cache[sid].add(r)
        return self.hypehypo_cache[sid]

    def cache_all_hypehypo(self):
        results = self.schema.sss.select(columns=['linkid', 'dpos', 'dsynsetid', 'dsensekey', 'dwordid', 'ssynsetid'])
        for result in results:
            self.hypehypo_cache[result.ssynsetid].update(result)

    word_cache = dict()

    def get_hypehypo_text(self, sid):
        senses = self.get_hypehypo(sid)
        if not senses:
            return []
        else:
            lemmas = []
            wordids = [sense.wordid for sense in senses]
            need_to_find = []
            for wordid in wordids:
                if wordid in WordnetSQL.word_cache:
                    lemmas.append(WordnetSQL.word_cache[wordid])
                else:
                    need_to_find.append(str(wordid))
            if len(need_to_find) > 0:
                # search in database
                query = '''SELECT wordid, lemma FROM words
                            WHERE wordid in (%s);''' % ','.join(need_to_find)
                with self.schema.ds.open() as exe:
                    result = exe.execute(query).fetchall()
                    for (wordid, lemma) in result:
                        WordnetSQL.word_cache[wordid] = lemma
                        lemmas.append(lemma)
            return lemmas

    def cache_all_words(self):
        query = '''SELECT wordid, lemma FROM words'''
        with self.schema.ds.open() as exe:
            result = exe.execute(query).fetchall()
            for (wordid, lemma) in result:
                WordnetSQL.word_cache[wordid] = lemma

    sense_map_cache = None

    def all_senses(self):
        if WordnetSQL.sense_map_cache:
            return WordnetSQL.sense_map_cache
        _query = """SELECT lemma, pos, synsetid, sensekey, definition, tagcount
                                FROM wordsXsensesXsynsets ORDER BY lemma, pos, tagcount DESC;"""
        with self.schema.ds.open() as exe:
            result = exe.execute(_query).fetchall()
            # Build lemma map
            lemma_map = {}
            for (lemma, pos, synsetid, sensekey, definition, tagcount) in result:
                sinfo = Synset(synsetid, tagcount=tagcount, lemma=lemma)
                # add to map
                if lemma not in lemma_map:
                    lemma_map[lemma] = []
                lemma_map[lemma].append(sinfo)
        # Done caching
        WordnetSQL.sense_map_cache = lemma_map
        return lemma_map

    lemma_list_cache = dict()

    def search_senses(self, lemma_list, pos=None, a_conn=None):
        if len(lemma_list) == 0:
            return list()

        CACHE_JOIN_TOKEN = '|\t' * 12
        cache_key = CACHE_JOIN_TOKEN.join(lemma_list)
        # caching method
        if cache_key in WordnetSQL.lemma_list_cache:
            return WordnetSQL.lemma_list_cache[cache_key]

        # Build query lemma, pos, synsetid, sensekey, definition, tagcount
        _query = """SELECT lemma, pos, synsetid, sensekey, definition, tagcount
                                FROM wordsXsensesXsynsets
                                WHERE (%s) """ % 'or '.join(["lemma=?"] * len(lemma_list))
        _args = list(lemma_list)
        if pos:
            _query += " and pos = ?"
            _args.append(pos)
        # Query
        if a_conn:
            conn = a_conn
        else:
            conn = self.get_conn()
        c = conn.cursor()
        result = c.execute(_query, _args).fetchall()

        # Build results
        senses = []
        for (lemma, pos, synsetid, sensekey, definition, tagcount) in result:
            senses.append(Synset(synsetid, tagcount=tagcount, lemma=lemma))
        if not a_conn:
            conn.close()

        # store to cache
        WordnetSQL.lemma_list_cache[cache_key] = senses
        return senses
    
    sense_cache = dict()
    def get_all_senses(self, lemma, pos=None):
        '''Get all senses of a lemma

        Return an object with the type of lelesk.SenseInfo
        '''
        if (lemma, pos) in WordnetSQL.sense_cache:
            return WordnetSQL.sense_cache[(lemma, pos)]
        conn = self.get_conn()
        c = conn.cursor()
        if pos:
            if pos == 'a':
                result = c.execute("""SELECT pos, synsetid, sensekey, definition, tagcount 
                                    FROM wordsXsensesXsynsets
                                    WHERE lemma = ? and pos IN ('a', 's');""", (lemma,)).fetchall() 
            else:
                result = c.execute("""SELECT pos, synsetid, sensekey, definition, tagcount 
                                    FROM wordsXsensesXsynsets
                                    WHERE lemma = ? and pos = ?;""", (lemma, pos)).fetchall()   
        else:
            result = c.execute("""SELECT pos, synsetid, sensekey, definition, tagcount 
                                FROM wordsXsensesXsynsets
                                WHERE lemma = ?;""", (lemma,)).fetchall()
        senses = []
        # print("Found result: %s" % len(result))
        for (rpos, synsetid, sensekey, definition, tagcount) in result:
            if rpos == 's':
                rpos = 'a'
            senses.append(SenseInfo(SynsetID.from_string(synsetid), sensekey, '', definition, tagcount))
        conn.close()
        WordnetSQL.sense_cache[(lemma, pos)] = senses
        return senses
        
    def cache_all_sense_by_lemma(self):
        with self.get_conn() as conn:
            c = conn.cursor()
            result = c.execute("""SELECT lemma, pos, synsetid, sensekey, definition FROM wordsXsensesXsynsets;""").fetchall()

            for (lemma, pos, synsetid, sensekey, definition) in result:
                if lemma not in WordnetSQL.sense_cache:
                    WordnetSQL.sense_cache[lemma] = []
                WordnetSQL.sense_cache[lemma].append(SenseInfo(SynsetID.from_string(synsetid), sensekey, '', definition))

    def get_gloss_by_sk(self, sk):
        sid = self.get_senseinfo_by_sk(sk).get_full_sid()
        return self.get_gloss_by_id(sid)
    
    gloss_cache = dict()
    def get_gloss_by_id(self, sid):
        if sid in WordnetSQL.gloss_cache:
            return WordnetSQL.gloss_cache[sid]
        if not sid:
            return None
        gloss_file = self.search_by_id(sid)
        if not gloss_file:
            return None
        gloss_file_loc = os.path.join(self.standoff, gloss_file + '-wngloss.xml')
        gloss_data = XMLCache.parse(gloss_file_loc).find("./{http://www.xces.org/schema/2003}struct[@id='%s']" % (sid + '_d',))
        # Build gloss object
        a_sense = SenseGloss(gloss_data.get('id'), 
                            gloss_data.get('from'), 
                            gloss_data.get('to'), 
                            gloss_data.get('type'))
        # Retrieve each gloss token
        ann_file_loc = os.path.join(self.standoff, gloss_file + '-wnann.xml')
        ann = XMLCache.parse(ann_file_loc).findall("./{http://www.xces.org/schema/2003}struct")
        wnword_file_loc = os.path.join(self.standoff, gloss_file + '-wnword.xml')
        wnword = XMLCache.parse(wnword_file_loc)
        if len(ann) > 0:
            for elem in ann:
                if elem.attrib['id'].startswith(sid):
                    features = dd(lambda: '')
                    features['sid'] = elem.get('id')
                    features['sfrom'] = elem.get('from')
                    features['sto'] = elem.get('to')
                    features['stype'] = elem.get('type')
                    # We only use the gloss part
                    #if int(features['sfrom']) > int(a_sense.sto):
                    #   break
                    for feat in elem:
                        features[feat.get('name')] = feat.get('value')
                    # Look for sensekey if available
                    wnsk = wnword.findall("./{http://www.xces.org/schema/2003}struct[@id='%s']/*[@name='wnsk']" % (elem.get('id'),))
                    if len(wnsk) == 1:
                        features['wnsk'] = wnsk[0].get('value')
                    a_sense.tokens.append(GlossInfo.from_dict(features))
            # Read glosses data
            WordnetSQL.gloss_cache[sid] = a_sense
            return a_sense
        else:
            WordnetSQL.gloss_cache[sid] = None
            return None
        pass

    # Search a synset by ID
    def search_by_id(self, synset_id):
        # print 'searching %s' % synset_id
        if synset_id in self.sid_index:
            return self.sid_index[synset_id]
        else:
            return None

    # Search a synset by sensekey
    def search_by_sk(self, wnsk):
        if wnsk in self.sk_index:
            return self.sk_index[wnsk]
        else:
            return 'N/A'

    @staticmethod
    def get_default(auto_cache=True):
        wnsql = WordnetSQL(YLConfig.WORDNET_30_PATH, YLConfig.WORDNET_30_GLOSSTAG_PATH)
        # Cache everything into memory if needed
        if auto_cache:
            wnsql.cache_all_words()
            wnsql.cache_all_sense_by_lemma()
            wnsql.cache_all_hypehypo()
            wnsql.cache_all_sensekey()
        return wnsql
