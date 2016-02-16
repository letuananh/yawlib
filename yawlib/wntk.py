#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A tool for converting Gloss WordNet into SQLite
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
from lxml import etree
from collections import defaultdict as dd
from collections import namedtuple

from chirptext.leutile import StringTool, Counter, Timer, uniquify, header, FileTool

from .config import YLConfig
from .helpers import dump_synsets, dump_synset, get_synset_by_id, get_synset_by_sk, get_synsets_by_term
from .glosswordnet import XMLGWordNet, SQLiteGWordNet, Gloss
from .wordnetsql import WordNetSQL as WSQL
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
GLOSSTAG_XML_FILES = [
    os.path.join(YLConfig.WORDNET_30_GLOSSTAG_PATH , 'merged', 'adv.xml')
    ,os.path.join(YLConfig.WORDNET_30_GLOSSTAG_PATH, 'merged', 'adj.xml')
    ,os.path.join(YLConfig.WORDNET_30_GLOSSTAG_PATH, 'merged', 'verb.xml')
    ,os.path.join(YLConfig.WORDNET_30_GLOSSTAG_PATH, 'merged', 'noun.xml')
    ]

#-----------------------------------------------------------------------

class GlossTagPatch:
    def __init__(self):
        self.patched = [ '00012779-r', '00022401-r', '00098147-a', '01032029-a', '01909077-a', '02171024-a', '02404081-a', '02773862-a', '00227165-v', '00515154-v', '00729109-v', '00781000-v', '01572728-v', '01618547-v', '01915365-v', '02162162-v', '02358327-v', '02545045-v', '02646064-v', '02655135-v', '02685390-v', '02711114-v', '03501288-n', '05845888-n', '07138504-n', '07138736-n', '08145553-n', '13855627-n', '13997529-n', '14457976-n', '15021189-n' ]
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

def test_extract_xml():
    ''' Test data extraction from XML file
    ''' 
    xmlwn = XMLGWordNet()
    xmlwn.read(MOCKUP_SYNSETS_DATA)
    
    for ss in xmlwn.synsets[:5]:
        dump_synset(ss)

def test_gwn_access():
    ''' Testing wordnetsql module
    '''
    db = WSQL(WORDNET_30_PATH)

    sinfo = db.get_senseinfo_by_sk('pleasure%1:09:00::')
    print(sinfo)
    hypehypos = db.get_hypehypo(sinfo.synsetid)
    for hh in hypehypos:
        print(hh)

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

# '00022401-r' : ['of the distant or comparatively distant past', '"We met once long ago"', '"they long ago forsook their nomadic life"', '"left for work long ago"', '"he has long since given up mountain climbing"', '"This name has long since been forgotten"', '"lang syne" is Scottish']
 
# ,'00996448-a' : ['not encouraging or approving or pleasing', '"unfavorable conditions"', '"an unfavorable comparison"', '"unfavorable comments"', '"unfavorable impression"']

# ,'01028623-a' : ['adapted to various purposes, sizes, forms, operations', '"universal wrench"', '"universal chuck"', '"universal screwdriver"']

# ,'01304802-a' : ['giving advice', '"an advisory memorandum"', '"his function was purely consultative"']

# ,'01475282-a' : ['hard to control', '"a difficult child"', '"an unmanageable situation"']

# ,'01824244-a' : ['having a strong physiological or chemical effect', '"a potent toxin"', '"potent liquor"', '"a potent cup of tea"', '"a stiff drink"']

# ,'01909077-a' : ['(of color) discolored by impurities; not bright and clear', '"dirty" is often used in combination', '"a dirty (or dingy) white"', '"the muddied grey of the sea"', '"muddy colors"', '"dirty-green walls"', '"dirty-blonde hair"']

# ,'01985976-a' : ['capable of mentally absorbing', '"assimilative processes"', '"assimilative capacity of the human mind"']

# ,'02026785-a' : ['high in mineral content; having a high proportion of fuel to air', '"a rich vein of copper"', '"a rich gas mixture"']

# ,'02056880-a' : ['not concerned with or devoted to religion', '"sacred and profane music"', '"secular drama"', '"secular architecture"', '"children being brought up in an entirely profane environment"']

}

def split_gloss(ss):
    sid = ss.get_synsetid()
    if sid in MANUAL_SPLIT:
        return MANUAL_SPLIT[sid]

    gl = ss.raw_glosses[0].gloss # raw gloss
    # [2016-02-15 LTA] Some commas are actually semicolons
    gl = gl.replace('", "', '"; "')     
    parts = [ x.strip() for x in gl.split(';') if len(x.strip()) > 0 ]

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

def combine_glosses(orig_glosses):
    defs    = []
    exs     = []

    for gloss in orig_glosses:
        if gloss.origid is None or gloss.origid.endswith('d'):
            if len(exs) > 0:
                print("WARNING: aux or def after examples")
            defs.append(gloss)
        else:
            idparts = gloss.origid.split('_')
            if len(idparts) == 2 and idparts[1].startswith('ex'):
                exs.append(gloss)
            else:
                print("WARNING: Invalid origid [%s]" % (gloss.origid,))

    # Create def gloss
    g = Gloss(defs[0].synset, defs[0].origid, defs[0].cat, defs[0].gid)
    for other in defs[1:]:
        # update origid, cat and gid if needed
        if g.origid is None: g.origid = other.origid
        if g.cat is None: g.origid = other.cat
        if g.gid is None: g.origid = other.gid    
        g.items += other.items
        g.tags += other.tags
        g.groups += other.groups
    return [ g ] + exs

def dev_mode(wng_db_loc):
    ''' Just a dummy method for quick calling
    '''
    # test_extract_xml()   # Demo extracting Gloss WordNet XML file 
    # test_gwn_access()    # Demo accessing WN30 SQLite
    #test_skmap_gwn_wn30() # Comparing sensekeys between GWN and WN30SQLite

    db = WSQL(WORDNET_30_PATH)
    # print("Get freq of a synset")
    # c = db.get_tagcount('100002684')
    # print(c)

    t = Timer()

    xmlwn = XMLGWordNet()
    xmlwn.read(MOCKUP_SYNSETS_DATA)

    ss = xmlwn.synsets[1]
    # print("First synset:")
    # dump_synset(ss)
    
    header("Gloss info")
    print(ss.raw_glosses[0].gloss)
    glosses = combine_glosses(ss.glosses)
    for gl in glosses:
        print("#")
        print("    > %s" % gl.items)
        print("    > %s" % gl.tags)
        print("    > %s" % gl.groups)
        for item in gl.items:
            print(item)
        print('***')
        for tag in gl.tags:
            print(tag)
    raw_text = ss.raw_glosses[0].gloss
    print(ss.glosses)

    gwn = SQLiteGWordNet(wng_db_loc)
    t.start("Cache all SQLite synsets")
    synsets = gwn.all_synsets()
    # synsets = xmlwn.synsets
    t.end("Done caching")
    
    c = Counter()
    with open("data/WRONG_SPLIT.txt", 'w') as wrong, open('data/SYNSET_TO_FIX.txt', 'w') as sslist:
        glpatch = GlossTagPatch()
        for ss in synsets:
            if ss.get_synsetid() in glpatch.patched:
                ss = glpatch.synset_map[ss.get_synsetid()]
            parts = split_gloss(ss)
            glosses = combine_glosses(ss.glosses)
            if len(parts) != len(glosses):
                # print("WARNING")
                # dump_synset(ss)
                sslist.write("%s\n" % (ss.get_synsetid()))
                wrong.write("[%s] -- %s\n" % (ss.get_synsetid(), ss.raw_glosses[0].gloss,))
                wrong.write("len(parts) = %s\n" % (len(parts)))
                for idx, part in enumerate(parts):
                    wrong.write("    -- %s: %s\n" % (str(idx).rjust(3), part,))
                wrong.write("len(glosses) = %s\n" % (len(glosses)))
                for idx, gl in enumerate(glosses):
                    wrong.write('    >> %s: %s\n' % (str(idx).rjust(3), gl.items,))
                c.count("WRONG")
                wrong.write("'%s' : %s\n\n" % (ss.get_synsetid(), parts,))
            else:
                c.count("OK")
    c.summarise()
    print("See data/SYNSET_TO_FIX.txt for more information")
    
    # header("Test smart search")
    # smart_search(ss.raw_glosses[0].gloss, [ x.text for x in ss.glosses[0].items ])

    # print("#------------------")
    # for ss in xmlwn.synsets:
    #     sent = ss.raw_glosses[0].gloss
    #     # print(sent)
    #     # smart_search(sent, [ x.text for x in ss.glosses[0].items ])
    #     smart_search(sent, ss.glosses[0].items, lambda x : x.text)
    print("Done!")

def smart_search(sentence, words, getitem=lambda x:x):
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
            hint = sentence[pos:pos+10] + '...' if pos+10 < len(sentence) else sentence[pos:pos+10]
            print('\t[%s] word=[%s] pos=Not found (starting at [%s] => [%s])' % (wid,word,pos,hint))
            prob = True
        else:
            # print("\tword=%s pos=%s" % (word, idx))
            asent.words.append(Word(word, idx, idx + len(word_text)))
            pos = idx + len(word_text)
    if prob:
        print(sentence)
        print([ (idx,w) for idx,w in enumerate(asent.words) ])
    return asent

#--------------------------------------------------------

def read_xmlwn(merged_folder):
    header("Extracting Gloss WordNet (XML)")
    t = Timer()
    xmlgwn = XMLGWordNet()
    for xml_file in GLOSSTAG_XML_FILES:
        t.start('Reading file: %s' % xml_file)
        xmlgwn.read(xml_file)
        t.end("Extraction completed %s" % xml_file)
    return xmlgwn

def xml2db(merged_folder, db):
    ''' Convert a XML file of Gloss WordNet into SQLite
    '''
    t = Timer()

    header("Extracting Gloss WordNet (XML)")
    xmlgwn = read_xmlwn(merged_folder)

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
    xml2db(merged_folder, db)
    pass

def export_ntumc(wng_loc, wng_db_loc):
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

    gwn = SQLiteGWordNet(wng_db_loc)
    wn = WSQL(WORDNET_30_PATH)
    xmlwn = read_xmlwn(merged_folder)

    t = Timer()
    t.start("Retrieving synsets from DB")

    # mockup data
    synsets = xmlwn.synsets
    # synsets = mockup_synsets()
    # synsets = gwn.all_synsets()
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
        for ss in synsets:
            sent = ss.raw_glosses[0].gloss
            sent_file.write('%s\t%s\n' % (sentid, sent,))
            # print(sent)
            words = []
            wordid = 0
            conceptid = 0
            # [2016-02-01] There is an error in glossitem for synset 01179767-a (a01179767)
            for gl in ss.glosses:
                wordid_map = {}
                conceptid_map = {}
                coll_map = dd(list)
                cwl = []
                CWL = namedtuple("CWL", "cid wid".split())
                for item in gl.items:
                    if item.origid == 'a01179767_wf37':
                        item.text = "'T"
                words += gl.items
            asent = smart_search(sent, words, lambda x: x.text)
            outfile.write('INSERT INTO sent (sid,docID,pid,sent,comment,usrname) VALUES(%s,%s,"","%s","[WNSID=%s]","letuananh");\n' % ( sentid, docid, asent.sent.replace('"', '""').replace("'", "''"), ss.get_synsetid()) )
            outfile.write('-- WORDS\n')
            for word in asent.words:
                testword = sent[word.cfrom:word.cto]
                if testword != word.data.text:
                    print("WARNING: Expected [%s] but found [%s]" % (word.text, testword))
                outfile.write('INSERT INTO word (sid, wid, word, pos, lemma, cfrom, cto, comment, usrname) VALUES (%s, %s, "%s", "%s", "", %s, %s, "", "letuananh");\n' % (sentid, wordid, word.data.text.replace('"', '""').replace("'", "''"), word.data.pos, word.data.lemma, word.cfrom, word.cto))
                wordid_map[wordid] = word.data.origid
                wordid_map[word.data.origid] = wordid
                if word.data.coll:
                    coll_map[word.data.coll].append(word.data.origid)
                word_file.write('%s\t%s\t%s\t%s\t%s\n' % (sentid, word.data.text, word.cfrom, word.cto, word.data.lemma))
                wordid += 1
            outfile.write('-- CONCEPTS\n')
            for gl in ss.glosses:
                for tag in gl.tags:
                    # tag = synsetid in NTU format (12345678-x)
                    if tag.sk:
                        tagged_ss = gwn.get_synset_by_sk(tag.sk)
                        if not tagged_ss:
                            print("sk[%s] could not be found" % (tag.sk))
                        elif len(tagged_ss) > 1:
                            print("Too many synsets found for sk[%s]" % (tag.sk))
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

SYNSETS_TO_EXTRACT = [
'00010466-r', '00015471-r', '00022401-r', '00025290-r', '00025559-r', '00025728-r', '00074641-r', '00121135-r', '00027074-a', '00098147-a', '00204249-a', '00326608-a', '00532560-a', '00767626-a', '01032029-a', '01493423-a', '01540871-a', '01623360-a', '01644225-a', '01644541-a', '01909077-a', '02171024-a', '02404081-a', '02773862-a', '00515154-v', '00729109-v', '00781000-v', '01572728-v', '01915365-v', '02162162-v', '02604760-v', '02655135-v', '02711114-v', '02674482-n', '05495172-n', '07138504-n', '07138736-n', '07139316-n', '07569644-n', '08145553-n', '09405169-n', '13780719-n', '13997529-n', '14457976-n', '15021189-n'
]

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

    wng_loc = args.wng_location if args.wng_location else WORDNET_30_GLOSSTAG_PATH
    wng_db_loc = args.wng_db if args.wng_db else (args.glosswn if args.glosswn else WORDNET_30_GLOSS_DB_PATH)
    wn30_loc = args.wnsql if args.wnsql else WORDNET_30_PATH

    # Now do something ...
    if args.dev:
        dev_mode(wng_db_loc)
    elif args.extract:
        extract_synsets_xml()
    elif args.create:
        convert(wng_loc, wng_db_loc, True)
    elif args.ntumc:
        export_ntumc(wng_loc, wng_db_loc)
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
