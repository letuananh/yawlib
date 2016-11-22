#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
YAWLib console application
Latest version can be found at https://github.com/letuananh/yawlib

Usage:
    # Search sysets by term (word form) = `love' and POS is verb
    python3 wntk.py -t 'love' -p 'v'

    # Search synsets by synset-id
    python3 wntk.py -s 'v01775535'

    # Search synsets by sensekey
    python3 wntk.py -k 'love%2:37:01::'

    # Create SQLite database for searching
    python3 wntk.py -c -i ~/wordnet/glosstag -g ~/wordnet/gwn.db

This script is used to be a part of lelesk project (https://github.com/letuananh/lelesk)

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
__copyright__ = "Copyright 2016, yawlib"
__credits__ = [ "Le Tuan Anh" ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

# import sys
import os.path
import argparse
import itertools
import logging
from lxml import etree
from collections import defaultdict as dd
from collections import namedtuple

from chirptext.leutile import StringTool, Counter, Timer, uniquify, header, FileTool

from .config import YLConfig
from .helpers import dump_synsets, dump_synset, get_synset_by_id, get_synset_by_sk, get_synsets_by_term
from .glosswordnet import XMLGWordNet, SQLiteGWordNet, Gloss
from .wordnetsql import WordNetSQL as WSQL

try:
    from fuzzywuzzy import fuzz
except Exception as e:
    logging.warning("fuzzywuzzy is not installed")
    pass
#-----------------------------------------------------------------------
# CONFIGURATION
#-----------------------------------------------------------------------
# >>> WARNING: Do NOT change these values here. Change config.py instead!
#
WORDNET_30_PATH          = YLConfig.WORDNET_30_PATH
WORDNET_30_GLOSSTAG_PATH = YLConfig.WORDNET_30_GLOSSTAG_PATH
WORDNET_30_GLOSS_DB_PATH = YLConfig.WORDNET_30_GLOSS_DB_PATH
DB_INIT_SCRIPT           = YLConfig.DB_INIT_SCRIPT
MOCKUP_SYNSETS_DATA      = FileTool.abspath('data/test.xml')
GLOSSTAG_NTUMC_OUTPUT    = FileTool.abspath('data/glosstag_ntumc')
GLOSSTAG_PATCH           = FileTool.abspath('data/glosstag_patch.xml')
glosstag_files = lambda x : [
    os.path.join(x, 'adv.xml')
    ,os.path.join(x, 'adj.xml')
    ,os.path.join(x, 'verb.xml')
    ,os.path.join(x, 'noun.xml')
    ]
MERGED_FOLDER            = os.path.join(WORDNET_30_GLOSSTAG_PATH , 'merged')
GLOSSTAG_XML_FILES       = glosstag_files(MERGED_FOLDER)
MISALIGNED               = FileTool.abspath('data/misaligned.xml')

#-----------------------------------------------------------------------

class GlossTagPatch:
    def __init__(self):
        self.patched = [ '01179767-a', '00022401-r', '00100506-a', '00710741-a', '01846815-a', '02171024-a', '02404081-a', '02773862-a', '00515154-v', '00729109-v', '00781000-v', '01572728-v', '01593254-v', '01915365-v', '02162162-v', '02655135-v', '02711114-v', '00442115-n', '01219722-n', '07192129-n', '13997529-n', '14457976-n',  '00781000-v', '02655135-v' ]
        xmlwn = XMLGWordNet()
        xmlwn.read(GLOSSTAG_PATCH)
        self.synsets = xmlwn.synsets
        self.synset_map = {}
        for ss in self.synsets:
            self.synset_map[ss.get_synsetid()] = ss
        pass

def cache_all_synsets(wng_db_loc):
    ''' Cache all Gloss Synset (SQLite) to database
    '''
    t = Timer()
    t.start("Caching synsets")
    db = SQLiteGWordNet(wng_db_loc)
    synsets = db.all_synsets()
    t.end("Done caching")

    db = WSQL(WORDNET_30_PATH)
    t.start("Start caching stuff ...")
    # This should take less than 5 secs to run
    db.cache_all_sensekey()
    #------------------------------------------
    # This should take less than 25 secs to run
    db.cache_all_hypehypo()
    t.end("Done caching!")

#-----------------------------------------------------------------------

def mockup_synsets():
    ''' Retrieve mockup synsets from ./data/test.xml
    '''
    xmlwn = XMLGWordNet()
    xmlwn.read(MOCKUP_SYNSETS_DATA)
    synsets = xmlwn.synsets
    return synsets

def test_skmap_gwn_wn30():
    ''' Comparing sensekeys between GWN and WN30SQLite
    '''
    gwn = SQLiteGWordNet(wng_db_loc)
    wn = WSQL(WORDNET_30_PATH)

    t = Timer()
    t.start('Caching WN30 sensekey map')
    wnsks = wn.get_all_sensekeys()
    wn_skmap = {}
    wn_sidmap = dd(list)
    # map by sensekeys and synsetid
    for item in wnsks:
        wn_skmap[item.sensekey] = item.synsetid
        wn_sidmap[str(item.synsetid)[1:]].append(item.sensekey)
    t.end("Done WN30")

    t.start('Caching GWN sensekey map')
    gwn_ss = gwn.get_all_sensekeys()
    gwn_skmap = {}
    for item in gwn_ss:
        gwn_skmap[item.sensekey] = item.sid
    t.end("Done GWN")

    t.start('Caching GWN tagged sensekey')
    gwn_tags = gwn.get_all_sensekeys_tagged()
    t.end("Done tagged sensekey")

    print("wn30 sensekeys: %s" % len(wnsks))
    print("gwn synsets   : %s" % len(gwn_ss))
    print("All tagged sk : %s" % len(gwn_tags))

    c = Counter()
    for tag in gwn_tags:
        if tag not in gwn_skmap:
            print("sk [%s] does not exist in GWN" % tag)
            c.count("GWN Not Found")
        else:
            c.count("GWN Found")
        if tag not in wn_skmap:
            if tag in gwn_skmap:
                gwn_sid = gwn_skmap[tag][1:]
                # print("Searching %s" % (gwn_sid))
                if gwn_sid in wn_sidmap:
                    candidates = wn_sidmap[gwn_sid]
                    newsks = set()
                    for cand in candidates:
                        if cand not in gwn_skmap:
                            newsks.add(cand)
                    # print("Found but changed: %s => %s" % (tag, newsks))
                    c.count("WN30 Found derivative")                    
                else:
                    c.count("WN30 Not Found At all")
                    print("sk [%s] does not exist in WN30 at all ..." % tag)    
            else:
                c.count("WN30 & GWN Not Found")
                print("sk [%s] does not exist in WN30" % tag)
        else:
            c.count("WN30 Found")
    c.summarise()

MANUAL_SPLIT = {

    '00781000-v' : ['continue talking', '"I know it\'s hard," he continued, "but there is no choice"', '"carry on--pretend we are not in the room"']

    ,'00011516-r' : ["(`ill' is often used as a combining form)", "in a poor or improper or unsatisfactory manner; not well", '"he was ill prepared"', '"it ill befits a man to betray old friends"', '"the car runs badly"', '"he performed badly on the exam"', '"the team played poorly"', '"ill-fitting clothes"', '"an ill-conceived plan"' ]
    ,'01179767-a' : ['being or having the nature of a god;', '"the custom of killing the divine king upon any serious failure of his...powers"-J.G.Frazier', '"the divine will"', '"the divine capacity for love"', '"\'tis wise to learn; \'tis God-like to create"-J.G.Saxe']

}

#being or having the nature of a god; "the custom of killing the divine king upon any serious failure of his...powers"-J.G.Frazier; "the divine will"; "the divine capacity for love"; "'tis wise to learn; 'tis God-like to create"-J.G.Saxe

def split_gloss(ss, expected_length):
    """ Split gloss (raw text) into many sentences
    """
    sid = ss.get_synsetid()
    if sid in MANUAL_SPLIT:
        return MANUAL_SPLIT[sid]

    gl = ss.raw_glosses[0].gloss # raw gloss
    # [2016-02-15 LTA] Some commas are actually semicolons
    gl = gl.replace(', "', '; "').replace(': "', '; "').replace(':"', '; "')
    parts = [ x.strip() for x in gl.split(';') if len(x.strip()) > 0 ]
    if expected_length >= len(parts):
        return parts
    examples = []
    definition = []
    skip = False
    for partid, part in enumerate(parts):
        if part.startswith('"') or part.endswith('"') or (len(examples) > 0  and part.startswith('(') and part.endswith(')')):
            if skip:
                skip = False
                continue
            if partid < len(parts)-1 and part.startswith('"') and not part.endswith('"') and not parts[partid+1].startswith('"') and parts[partid+1].endswith('"'):
                # merge
                examples.append(part + '; ' + parts[partid+1])
                skip = True
            elif part.startswith('(') and part.endswith(')'):
                # merge to the last example
                examples[len(examples)-1] += '; ' + part
            else:
                examples.append(part)
        else:
            if len(examples) > 0:
                # print("WARNING: abnormal part [%s] in gloss: %s" % (part, gl,))
                # print("   >> %s" % (ss.glosses,))
                pass
            definition.append(part)

    return [ '; '.join(definition) ] + examples

def combine_glosses(orig_glosses, ssid = None):
    ''' Combine wrongly split glosses 
    '''
    if ssid in [ '00022401-r', '00098147-a' ]:
        # ignore these synsets
        return orig_glosses
    defs    = []
    exs     = []

    for gloss in orig_glosses:
        if gloss.origid is None or gloss.origid.endswith('d'):
            if gloss.origid is None and len(exs) > 0:
                exs.append(gloss)
            else:
                defs.append(gloss)
        else:
            idparts = gloss.origid.split('_')
            if len(idparts) == 2 and idparts[1].startswith('ex'):
                exs.append(gloss)
            else:
                print("WARNING: Invalid origid [%s]" % (gloss.origid,))

    # Create def gloss
    g = Gloss(defs[0].synset, defs[0].origid, defs[0].cat, defs[0].gid)
    g.items = [ x for x in defs[0].items ]
    g.tags = [ x for x in defs[0].tags ]
    g.groups = [ x for x in defs[0].groups ]
    for other in defs[1:]:
        # update origid, cat and gid if needed
        if g.origid is None: g.origid = other.origid
        if g.cat is None: g.origid = other.cat
        if g.gid is None: g.origid = other.gid    
        g.items += other.items
        g.tags += other.tags
        g.groups += other.groups

    if 'killed' in orig_glosses[0].items[0].text:
        print ([ x.items for x in ([g] + exs)])

    return [ g ] + exs

SplitData = namedtuple('SplitData', ['ss', 'sents', 'glosses', 'aligned'])

def prepare_for_ntumc(ss, glpatch=None):
    """ Split glosses into sentences (for importing into NTU-MC)
    """
    if glpatch and ss.get_synsetid() in glpatch.patched:
        ss = glpatch.synset_map[ss.get_synsetid()]

    sents = split_gloss(ss, len(ss.glosses))
    glosses = ss.glosses
    if len(glosses) != len(sents):
        # try to combine glosses smartly
        glosses = combine_glosses(ss.glosses, ss.get_synsetid())
        if len(glosses) != len(sents) and len(glosses) == len(ss.glosses):
            # need to relax split_gloss method a bit
            sents = split_gloss(ss, len(ss.glosses))

    try:
        aligned = []
        for (sent, gl) in zip(sents, glosses):
            gltext = ' '.join([ x.text for x in gl.items ]).replace(';', '')
            if fuzz.ratio(sent, gltext) > 80:
                aligned.append((sent, gl))
            else:
                for gl in glosses:
                    gltext = ' '.join([ x.text for x in gl.items ]).replace(';', '')
                    if fuzz.ratio(sent, gltext) > 80:
                        aligned.append((sent, gl))
                        break
        if len(aligned) < len(sents):
            logging.error("Invalid alignment in synset %s" % (ss.get_synset_by_id(),))
    except Exception as e:
        aligned = list(zip(sents, glosses))
        pass
            
    return SplitData(ss, sents, glosses, aligned)

def dev_mode(wng_db_loc, mockup=True):
    ''' Just a dummy method for quick calling
    '''
    # test_extract_xml()   # Demo extracting Gloss WordNet XML file 
    # test_gwn_access()    # Demo accessing WN30 SQLite
    # test_skmap_gwn_wn30() # Comparing sensekeys between GWN and WN30SQLite

    # test_alignment(wng_db_loc, mockup)
    # fix_misalignment()
    glosstag2txt(wng_db_loc)


def glosstag2txt(wng_db_loc):
    print("glosstag")
    gwn = SQLiteGWordNet(wng_db_loc)
    synsets = gwn.all_synsets()
    print("Synset count: %s" % (len(synsets),))

def fix_misalignment():
    xmlwn = XMLGWordNet()
    xmlwn.read(MISALIGNED)
    synsets = xmlwn.synsets
    glpatch = GlossTagPatch()
    with open('data/temp.txt', 'w') as outfile:
        for ss in synsets:
            outfile.write("Synset ID: %s\n" % (ss.get_synsetid(),))
            (ss,sents,glosses, aligned) = prepare_for_ntumc(ss, glpatch)
            outfile.write('RAW: %s' % (ss.raw_glosses[0].gloss))
            invalid = False
            for sent, gl in aligned:
                gltext = ' '.join([ x.text for x in gl.items ]).replace(';', '')
                match_score = fuzz.ratio(sent, gltext)
                outfile.write('    [%s] %s -- %s\n' % (match_score, sent, gl.items))
                if match_score < 80:
                    outfile.write("WARNING [%s]: %s >><< %s\n" % (ss.get_synsetid(), sent, gltext))
            outfile.write('\n--\n')
        
    print("%s synsets to be fixed" % (len(synsets)))
    print("See data/temp.txt for more information")

def test_alignment(wng_db_loc, mockup=True):
    t = Timer()
    t.start("Cache all SQLite synsets")
    if mockup:
        xmlwn = XMLGWordNet()
        xmlwn.read(MOCKUP_SYNSETS_DATA)
        synsets = xmlwn.synsets
    else:
        logging.info("Using SQLiteGWordNet (%s)" % (WORDNET_30_PATH))
        db = WSQL(WORDNET_30_PATH)
        gwn = SQLiteGWordNet(wng_db_loc)
        synsets = gwn.all_synsets()
    t.end("Done caching")
    
    c = Counter()
    with open("data/WRONG_SPLIT.txt", 'w') as wrong, open('data/SYNSET_TO_FIX.txt', 'w') as sslist, open('data/INVALID_ALIGNMENT.txt', 'w') as invalidfile:
        glpatch = GlossTagPatch()
        invalid_synsets = set()
        for ss in synsets:
            orig_glosses = [ x.text() for x in ss.glosses ]
            (ss,sents,glosses, aligned) = prepare_for_ntumc(ss, glpatch)
            if len(sents) != len(glosses):
                sslist.write("%s\n" % (ss.get_synsetid()))
                wrong.write("[%s] -- %s\n" % (ss.get_synsetid(), ss.raw_glosses[0].gloss,))
                wrong.write("len(sents) = %s\n" % (len(sents)))
                for idx, part in enumerate(sents):
                    wrong.write("    -- %s: %s\n" % (str(idx).rjust(3), part,))
                wrong.write("len(glosses) = %s\n" % (len(glosses)))
                for idx, gl in enumerate(glosses):
                    wrong.write('    >> %s: %s\n' % (str(idx).rjust(3), gl.items,))
                wrong.write("len(glosses_orig) = %s\n" % (len(ss.glosses)))
                for idx, gl in enumerate(ss.glosses):
                    wrong.write('    |  %s: %s\n' % (str(idx).rjust(3), gl.items,))

                c.count("WRONG")
                wrong.write("'%s' : %s\n\n" % (ss.get_synsetid(), sents,))
            else:
                c.count("OK")
            # check word alignment
            invalid = False
            for sent, gl in aligned:
                gltext = ' '.join([ x.text for x in gl.items ]).replace(';', '')
                if fuzz.ratio(sent, gltext) < 80:
                    print("WARNING [%s]: %s >><< %s" % (ss.get_synsetid(), sent, gltext))
                    invalid = True
            if invalid:
                invalid_synsets.add(ss.get_synsetid())
                invalidfile.write('%s\n' % (ss.get_synsetid(), ))
                invalidfile.write('Split raw gloss : \t%s\n' % (sents,))
                invalidfile.write('Orig glosses    : \t%s\n' % (orig_glosses,))
                invalidfile.write('Combined glosses: \t%s\n--\n\n' % ([ x.text() for x in glosses ],))
        invalidfile.write("\n\ninvalid_synsets=%s" % (invalid_synsets,))
    c.summarise()
    if c['WRONG'] > 0:
        print("See data/SYNSET_TO_FIX.txt and data/WRONG_SPLIT.txt for more information")
    else:
        print("Everything is OK!")
    
    print("Done!")

def smart_search(sentence, words, getitem=lambda x:x):
    ''' Link tokenized words back to original sentence
    '''
    pos = 0
    prob = False
    Word              = namedtuple("Word", "data cfrom cto")
    AnnotatedSentence = namedtuple("AnnotatedSentence", "sent words")
    asent = AnnotatedSentence(sentence, [])
    for wid, word in enumerate(words):
        word_text = getitem(word)
        if word_text == ";":
            continue
        idx = sentence.find(word_text, pos)
        if idx == -1:
            hint = sentence[pos:pos+20] + '...' if pos+20 < len(sentence) else sentence[pos:pos+10]
            logging.error('\t[%s] word=[%s] pos=Not found (starting at [%s] => [%s])' % (wid,word,pos,hint))
            prob = True
        else:
            # print("\tword=%s pos=%s" % (word, idx))
            asent.words.append(Word(word, idx, idx + len(word_text)))
            pos = idx + len(word_text)
    if prob:
        logging.error("context: %s" % (sentence,))
        logging.error("required: %s" % (words,))
        logging.error("words: %s\n" % ([ (idx,w) for idx,w in enumerate(asent.words) ],))
    return asent

#--------------------------------------------------------

def read_xmlwn(xml_filenames=GLOSSTAG_XML_FILES):
    ''' Read all synsets in XML format
    '''
    header("Extracting Gloss WordNet (XML)")
    print("XML files: %s" % (xml_filenames))
    t = Timer()
    xmlgwn = XMLGWordNet()
    for xml_file in xml_filenames:
        t.start('Reading file: %s' % xml_file)
        xmlgwn.read(xml_file)
        t.end("Extraction completed %s" % xml_file)
    return xmlgwn

def xml2db(xml_filenames, db):
    ''' Convert Gloss WordNet synsets in XML file(s) into SQLite
    '''
    t = Timer()

    header("Extracting Gloss WordNet (XML)")
    xmlgwn = read_xmlwn(xml_filenames)

    header("Inserting data into SQLite database")
    t.start()
    db.insert_synsets(xmlgwn.synsets)
    t.end('Insertion completed.')
    pass

def convert(wng_loc, wng_db_loc, createdb):
    ''' Convert Gloss WordNet into SQLite
    '''
    merged_folder = os.path.join(wng_loc, 'merged')
    
    print("Path to glosstag folder: %s" % (merged_folder))
    print("Path to output database: %s" % (wng_db_loc))
    print("Script to execute: %s" % (DB_INIT_SCRIPT))

    if os.path.isfile(wng_db_loc):
        print("DB file exists (%s | size: %s)" % (wng_db_loc,os.path.getsize(wng_db_loc)))
        answer = input("If you want to overwrite this file, please type CONFIRM: ")
        if answer != "CONFIRM":
            print("Script aborted!")
            exit()

    db = SQLiteGWordNet(wng_db_loc)
    if createdb:
        header('Preparing database file ...')
        db.setup(DB_INIT_SCRIPT)
    #--
    header('Importing data from XML to SQLite')
    xml2db(glosstag_files(merged_folder), db)
    pass

def export_ntumc(wng_loc, wng_db_loc, mockup=False):
    '''
    Export GlossTag to NTU-MC format
    '''
    print("Export GlossTag to NTU-MC")
    merged_folder         = os.path.join(wng_loc, 'merged')
#    glosstag_ntumc_script = wng_db_loc + ".ntumc.sql"
    glosstag_ntumc_script = GLOSSTAG_NTUMC_OUTPUT + ".script.sql"
    sent_file_path        = GLOSSTAG_NTUMC_OUTPUT + '_sent.csv'
    word_file_path        = GLOSSTAG_NTUMC_OUTPUT + '_word.csv'
    concept_file_path     = GLOSSTAG_NTUMC_OUTPUT + '_concept.csv'    

    print("Path to glosstag folder: %s" % (merged_folder))
    print("Path to glosstag DB    : %s" % (wng_db_loc))
    print("Output file            : %s" % (glosstag_ntumc_script))

    t = Timer()
    t.start("Retrieving synsets from DB")

    gwn = SQLiteGWordNet(wng_db_loc)
    if mockup:
        synsets = mockup_synsets()
        pass
    else:
        # synsets = gwn.all_synsets()
        wn = WSQL(WORDNET_30_PATH)
        xmlwn = read_xmlwn(GLOSSTAG_XML_FILES)
        synsets = xmlwn.synsets

    print("%s synsets found in %s" % (len(synsets), wng_db_loc))
    t.end()
    t.start("Generating cfrom cto ...")
    with open(glosstag_ntumc_script, 'w') as outfile, open(sent_file_path, 'w') as sent_file, open(word_file_path, 'w') as word_file, open(concept_file_path, 'w') as concept_file:
        outfile.write("""BEGIN TRANSACTION;
   INSERT INTO corpus (corpusID, corpus, title, language)
      VALUES (100, 'misc', "Miscellaneous", "eng"); 
   INSERT INTO doc (docid, doc, title, url, subtitle, corpusID) 
      VALUES(1000, "glosstag", "WordNet with Semantically Tagged Glosses", "http://wordnet.princeton.edu/glosstag.shtml", "", 100);
""")
        sentid = 1000000
        docid  = 1000
        glpatch = GlossTagPatch()
        for ss in synsets:
            (ss, sents, glosses, aligned) = prepare_for_ntumc(ss, glpatch)
            # sent = ss.raw_glosses[0].gloss
            
            # print(sent)
            # [2016-02-01] There is an error in glossitem for synset 01179767-a (a01179767)
            for sent, gl in aligned:
                wordid = 0
                conceptid = 0

                wordid_map = {}
                conceptid_map = {}

                sent_file.write('%s\t%s\n' % (sentid, sent,))
                coll_map = dd(list)
                cwl = []
                CWL = namedtuple("CWL", "cid wid".split())
                words = gl.items
                asent = smart_search(sent, words, lambda x: x.text)
                outfile.write('INSERT INTO sent (sid,docID,pid,sent,comment,usrname) VALUES(%s,%s,"","%s","[WNSID=%s]","letuananh");\n' % ( sentid, docid, asent.sent.replace('"', '""').replace("'", "''"), ss.get_synsetid()) )
                outfile.write('-- WORDS\n')
                for word in asent.words:
                    testword = sent[word.cfrom:word.cto]
                    if testword != word.data.text:
                        print("WARNING: Expected [%s] but found [%s]" % (word.text, testword))
                    outfile.write('INSERT INTO word (sid, wid, word, pos, lemma, cfrom, cto, comment, usrname) VALUES (%s, %s, "%s", "%s", "%s", %s, %s, "", "letuananh");\n' % (sentid, wordid, word.data.text.replace('"', '""').replace("'", "''"), word.data.pos, word.data.lemma, word.cfrom, word.cto))
                    wordid_map[wordid] = word.data.origid
                    wordid_map[word.data.origid] = wordid
                    if word.data.coll:
                        coll_map[word.data.coll].append(word.data.origid)
                    word_file.write('%s\t%s\t%s\t%s\t%s\n' % (sentid, word.data.text, word.cfrom, word.cto, word.data.lemma))
                    wordid += 1
                outfile.write('-- CONCEPTS\n')
                #for gl in ss.glosses:
                for tag in gl.tags:
                    # tag = synsetid in NTU format (12345678-x)
                    if tag.sk and tag.sk != 'purposefully_ignored%0:00:00::':
                        tagged_ss = gwn.get_synset_by_sk(tag.sk)
                        if not tagged_ss:
                            logging.info("sk[%s] could not be found" % (tag.sk))
                        elif len(tagged_ss) > 1:
                            logging.info("Too many synsets found for sk[%s]" % (tag.sk))
                        else:
                            # outfile.write("--%s\n" % (tagged_ss[0].get_synsetid(),))
                            outfile.write('INSERT INTO concept (sid, cid, clemma, tag, tags, comment, ntag, usrname) VALUES (%s, %s, "%s", "", "", "%s", "", "letuananh"); --sk=[%s]\n' % (sentid, conceptid, tag.lemma.replace('"', '""').replace("'", "''"), tagged_ss[0].get_synsetid(), tag.sk) );
                        conceptid_map[tag.origid] = conceptid
                        conceptid_map[conceptid]  = tag.origid
                        conceptid += 1
                        if tag.coll:
                            # multiword expression
                            for collword in coll_map[tag.coll]:
                                cwl.append(CWL(conceptid, wordid_map[collword]))
                        elif tag.item:
                            # normal tag
                            cwl.append(CWL(conceptid, wordid_map[tag.item.origid]))
                # outfile.write("/*%s*/\n" % (wordid_map))
                # outfile.write("/*%s*/\n" % (conceptid_map))
                # outfile.write("/*%s*/\n" % coll_map)
                # outfile.write("/*%s*/\n" % cwl)
                outfile.write('-- Concept-Word Links\n')
                for lnk in cwl:
                    outfile.write('INSERT INTO cwl (sid, wid, cid, usrname) VALUES (%s, %s, %s, "letuananh");\n' % (sentid, lnk.wid, lnk.cid))
                sentid += 1
                outfile.write('\n')
        # end for synsets
        outfile.write("END TRANSACTION;\n");
    t.end()
    print("Done!")
    
    pass

def to_synsetid(synsetid):
    return '%s-%s' % (synsetid[1:], synsetid[0])

SYNSETS_TO_EXTRACT = [ '09524555-n', '02426634-n', '10310516-n', '01804340-n', '09520498-n', '09585218-n', '10484526-n', '09571581-n', '08311933-n', '02423787-n', '04523993-n', '09582019-n', '01259594-n', '10528493-n', '01700075-a', '01929600-a', '01496592-a', '02291632-a', '07688757-n', '01992555-a', '00627849-a', '02259817-a', '02427337-n', '02067063-a', '01279183-a', '00974697-a', '04805304-n', '11889847-n', '10237935-n', '12222334-n', '05629381-n', '07689313-n', '01024812-a', '02430756-a', '02022162-v', '08641944-n', '07497019-n', '01502262-n', '15193271-n', '09490961-n', '00624285-n', '04455835-n', '01032029-a', '08225334-n', '02516148-a', '06006609-n', '09496673-n', '09517342-n', '09573561-n', '11889473-n', '01280576-a', '10750640-n', '09564371-n', '02822601-a', '07138736-n', '02422249-n', '04066023-n', '03550420-n', '02426054-n', '09555391-n', '15282032-n', '02155233-a', '09498186-n', '04323819-n', '00038623-a', '06609785-n', '07577538-n', '00253395-n', '01385255-a', '01040390-n', '00221553-a', '01824751-a', '12322359-n', '05626618-n', '09501737-n', '03976268-n', '01034685-n', '00660313-a', '00145713-r', '09560061-n', '05278922-n', '01859970-a', '03382708-n', '02421962-n', '10689306-n', '09498072-n', '01129920-n', '15258450-n', '10545682-n', '00814611-a', '09776522-n', '00071242-a', '07330560-n', '00100883-r', '00140542-a', '02217799-a', '09495732-n', '00605893-a', '09592734-n', '09180967-n', '12216028-n', '06032752-n', '02422561-n', '02430096-a', '09495619-n', '12223405-n', '09574926-n', '12385219-n', '10119953-n', '15229408-n', '00038462-a', '09579714-n', '06457796-n', '05613170-n', '09573145-n', '09920106-n', '08180484-n', '11202477-n', '01554510-a', '05065717-n', '03884778-n', '10840769-n', '15234587-n', '09549643-n', '01268426-a', '02532200-a', '00562823-n', '09566667-n', '02425393-n', '05824985-n', '09996920-n', '02649125-a', '03348454-n', '01612053-a', '12672497-n', '00558630-n', '09495849-n', '06509210-n', '09559404-n', '10750365-n', '09550125-n', '00728065-n', '09567309-n', '03120029-n', '04102162-n', '01302811-a', '00003316-v', '02038617-n', '02427958-n', '04460634-n', '10758713-n', '00252130-a', '09579994-n', '10219778-n', '08555883-n', '09829650-n', '09521994-n', '10240921-n', '00385946-r', '01630939-a', '01559294-n', '05144663-n', '09580673-n', '09566791-n', '00557419-n', '01929062-a', '00562643-n', '12853901-n', '13996211-n', '02428229-n', '05039106-n', '04605163-n', '11750855-n', '09549983-n', '00509377-a', '00458286-n', '10588860-n', '09593044-n', '04990781-n', '00727901-n', '00727743-n', '04055861-n', '09501198-n', '09498697-n', '02437853-a', '12486732-n', '09566436-n', '10158222-n', '00139919-n', '05082116-n', '02933954-a', '11455386-n', '01222100-a', '09829506-n', '03090598-n', '10557404-n', '00818678-n', '14342132-n', '02463990-v', '01971519-a', '06385434-n', '09682122-n', '10496393-n', '01929312-a', '01753721-n', '15204201-n', '03877472-n', '13813591-n', '15192890-n', '07281099-n', '14413831-n', '15231634-n', '07211503-n', '00230335-a', '02380819-a', '07543910-n', '14359459-n', '01142636-v', '13762836-n', '02107386-a', '00563360-v', '09494280-n', '02421308-n', '10375690-n', '14453290-n', '02010864-v', '00507913-v', '02531919-a', '09556580-n', '09566544-n', '00970081-a', '00509735-a', '04991389-n', '15227593-n', '07689003-n', '07851054-n', '07535532-n', '02818507-n', '00468587-r', '06804728-n', '02268133-a', '00456610-r', '00192523-a', '09520617-n', '09684352-n', '05628403-n', '09566320-n', '01193714-a', '02264752-v', '01235463-n', '02426339-n', '03085333-n', '12353604-n', '06464419-n', '10996533-n', '09575033-n' ]
# '00100506-a', '00710741-a', '01846815-a', '02171024-a', '02404081-a', '02773862-a', '00515154-v', '00729109-v', '00781000-v', '01572728-v', '01593254-v', '01915365-v', '02162162-v', '02655135-v', '02711114-v', '00442115-n', '01219722-n', '07192129-n', '13997529-n', '14457976-n'

def extract_synsets_xml():
    xfile_path = 'data/extract.xml'
    synsets = etree.Element("synsets")
    t = Timer()
    c = Counter()
    
    # Loop through elements in glosstag xml files
    t.start("Extracting synsets from glosstag ...")
    for xml_file in GLOSSTAG_XML_FILES: 
    # for xml_file in [ MOCKUP_SYNSETS_DATA ]:
        tree = etree.iterparse(xml_file)
        for event, element in tree:
            if event == 'end' and element.tag == 'synset':
                # do something to the element
                if to_synsetid(element.get('id')) in SYNSETS_TO_EXTRACT:
                    synsets.append(etree.fromstring(etree.tostring(element)))
                    c.count("FOUND")
                else:
                    c.count("IGNORED")
                # Clean up
                element.clear()
    t.end()
    c.summarise()

    # save the tree (nicely?)
    print("Writing synsets to %s" % (xfile_path,))
    with open(xfile_path, 'wb') as xfile:
        xfile.write(etree.tostring(synsets, pretty_print=True))
    print("Done!")

def main():
    '''Main entry of wntk

    '''
    # It's easier to create a user-friendly console application by using argparse
    # See reference at the top of this script
    parser = argparse.ArgumentParser(description="WordNet Toolkit - For accessing and manipulating WordNet")
    
    # Positional argument(s)
    # parser.add_argument('task', help='Task to perform (create/import/synset)')

    parser.add_argument('-i', '--wng_location', help='Path to Gloss WordNet folder (default = ~/wordnet/glosstag')
    parser.add_argument('-o', '--wng_db', help='Path to database file (default = ~/wordnet/glosstag.db')
    parser.add_argument('-c', '--create', help='Create DB and then import data', action='store_true')
    parser.add_argument('-m', '--mockup', help='Use mockup data in dev_mode', action='store_true')
    parser.add_argument('-n', '--ntumc', help='Extract GlossWordNet to NTU-MC', action='store_true')
    parser.add_argument('-d', '--dev', help='Dev mode (do not use)', action='store_true')
    parser.add_argument('-s', '--synset', help='Retrieve synset information by synsetid')
    parser.add_argument('-k', '--sensekey', help='Retrieve synset information by sensekey')
    parser.add_argument('-t', '--term', help='Retrieve synset information by term (word form)')
    parser.add_argument('-p', '--pos', help='Specify part-of-speech')
    parser.add_argument('-a', '--all', help='Cache all synsets', action='store_true')
    parser.add_argument('-w', '--wnsql', help='Location to WordNet SQLite 3.0 database')
    parser.add_argument('-g', '--glosswn', help='Location to Gloss WordNet SQLite database')
    parser.add_argument('-x', '--extract', help='Extract XML synsets from glosstag', action='store_true')

    # Optional argument(s)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    
    # Parse input arguments
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)

    wng_loc = args.wng_location if args.wng_location else WORDNET_30_GLOSSTAG_PATH
    wng_db_loc = args.wng_db if args.wng_db else (args.glosswn if args.glosswn else WORDNET_30_GLOSS_DB_PATH)
    wn30_loc = args.wnsql if args.wnsql else WORDNET_30_PATH

    # Now do something ...
    if args.dev:
        dev_mode(wng_db_loc, args.mockup)
    elif args.extract:
        extract_synsets_xml()
    elif args.create:
        convert(wng_loc, wng_db_loc, True)
    elif args.ntumc:
        export_ntumc(wng_loc, wng_db_loc, args.mockup)
    elif args.synset:
        get_synset_by_id(wng_db_loc, args.synset)
    elif args.sensekey:
        get_synset_by_sk(wng_db_loc, args.sensekey)
    elif args.all:
        cache_all_synsets(wng_db_loc)
    elif args.term:
        get_synsets_by_term(wng_db_loc, args.term, args.pos)
    else:
        parser.print_help()
    pass # end main()

if __name__ == "__main__":
    main()


# Note:
# How to use this tool
# ./main.py candidates -i "dear|a"
