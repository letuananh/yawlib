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
from collections import defaultdict as dd
from collections import namedtuple

from chirptext.leutile import StringTool, Counter, Timer, uniquify, header, FileTool

from .config import YLConfig
from .helpers import dump_synsets, dump_synset, get_synset_by_id, get_synset_by_sk, get_synsets_by_term
from .glosswordnet import XMLGWordNet, SQLiteGWordNet
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
#-----------------------------------------------------------------------

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

def dev_mode(wng_db_loc):
    ''' Just a dummy method for quick calling
    '''
    # test_extract_xml()   # Demo extracting Gloss WordNet XML file 
    # test_gwn_access()    # Demo accessing WN30 SQLite
    #test_skmap_gwn_wn30() # Comparing sensekeys between GWN and WN30SQLite

    db = WSQL(WORDNET_30_PATH)
    c = db.get_tagcount('100002684')
    print(c)

    xmlwn = XMLGWordNet()
    xmlwn.read(MOCKUP_SYNSETS_DATA)

    print("First synset:")
    ss = xmlwn.synsets[0]
    dump_synset(ss)
    
    print(ss.raw_glosses[0].gloss)
        
    for gl in ss.glosses:
        print("    > %s" % gl.items)
        print("    > %s" % gl.tags)
    raw_text = ss.raw_glosses[0].gloss
    print(ss.glosses)
    print("--------------------")
    smart_search(ss.raw_glosses[0].gloss, [ x.text for x in ss.glosses[0].items ])

    print("#------------------")

    for ss in xmlwn.synsets:
        sent = ss.raw_glosses[0].gloss
        # print(sent)
        # smart_search(sent, [ x.text for x in ss.glosses[0].items ])
        smart_search(sent, ss.glosses[0].items, lambda x : x.text)
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

def xml2db(xml_files, db):
    ''' Convert a XML file of Gloss WordNet into SQLite
    '''
    t = Timer()

    header("Extracting Gloss WordNet (XML)")
    xmlgwn = XMLGWordNet()
    for xml_file in xml_files:
        t.start('Reading file: %s' % xml_file)
        xmlgwn.read(xml_file)
        t.end("Extraction completed %s" % xml_file)

    header("Inserting data into đáng SQLite database")
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
    xmlfiles = [
        os.path.join(merged_folder, 'adv.xml')
        ,os.path.join(merged_folder, 'adj.xml')
        ,os.path.join(merged_folder, 'verb.xml')
        ,os.path.join(merged_folder, 'noun.xml')
    ]
    header('Importing data from XML to SQLite')
    xml2db(xmlfiles, db)
    pass

def export_ntumc(wng_loc, wng_db_loc):
    '''
    Export GlossTag to NTU-MC format
    '''
    print("Export GlossTag to NTU-MC")
    merged_folder         = os.path.join(wng_loc, 'merged')
    glosstag_ntumc_script = wng_db_loc + ".ntumc.sql"
    sent_file_path        = GLOSSTAG_NTUMC_OUTPUT + '_sent.csv'
    word_file_path        = GLOSSTAG_NTUMC_OUTPUT + '_word.csv'
    concept_file_path     = GLOSSTAG_NTUMC_OUTPUT + '_concept.csv'    

    print("Path to glosstag folder: %s" % (merged_folder))
    print("Path to glosstag DB    : %s" % (wng_db_loc))
    print("Output file            : %s" % (glosstag_ntumc_script))

    gwn = SQLiteGWordNet(wng_db_loc)
    wn = WSQL(WORDNET_30_PATH)

    t = Timer()
    t.start("Retrieving synsets from DB")

    # mockup data
    synsets = mockup_synsets()
    # synsets = gwn.all_synsets()
    print("%s synsets found in %s" % (len(synsets), wng_db_loc))
    t.end()
    t.start("Generating cfrom cto ...")
    with open(glosstag_ntumc_script, 'w') as outfile, open(sent_file_path, 'w') as sent_file, open(word_file_path, 'w') as word_file, open(concept_file_path, 'w') as concept_file:
        sentid = 1000000
        for ss in synsets:
            sent = ss.raw_glosses[0].gloss
            sent_file.write('%s\t%s\n' % (sentid, sent,))
            # print(sent)
            words = []
            # [2016-02-01] There is an error in glossitem for synset 01179767-a (a01179767)
            for gl in ss.glosses:
                for item in gl.items:
                    if item.origid == 'a01179767_wf37':
                        item.text = "'T"
                words += gl.items
            asent = smart_search(sent, words, lambda x: x.text)
            outfile.write("%s\n" % asent.sent)
            for word in asent.words:
                testword = sent[word.cfrom:word.cto]
                if testword != word.data.text:
                    print("WARNING: Expected [%s] but found [%s]" % (word.text, testword))
                outfile.write("%s [%s:%s] ==> |%s|\n" % (word.data.text, word.cfrom, word.cto, testword))
                word_file.write('%s\t%s\t%s\t%s\n' % (sentid, word.data.text, word.cfrom, word.cto))
            sentid += 1
        # end for synsets
    t.end()
    print("Done!")
    
    pass

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
