#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Extract information from several wordnet formats
Latest version can be found at https://github.com/letuananh/yawlib

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

import sys
import os.path
import argparse
import itertools
import logging
from lxml import etree
from collections import defaultdict as dd
from collections import namedtuple

from chirptext.leutile import StringTool
from chirptext.leutile import Counter
from chirptext.leutile import Timer
from chirptext.leutile import uniquify
from chirptext.leutile import header
from chirptext.leutile import FileTool

from yawlib import YLConfig
from yawlib import SynsetID
from yawlib.helpers import dump_synset
from yawlib.helpers import dump_synsets
from yawlib import XMLGWordNet
from yawlib import SQLiteGWordNet
from yawlib import WordNetSQL as WSQL

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


def get_gwn(args):
    gwn = SQLiteGWordNet(args.glossdb)
    return gwn


def get_wn(args):
    wn = WSQL(args.wnsql)
    return wn


def glosstag2ntumc(args):
    print("Extracting Glosstag to NTU-MC")
    show_info(args)
    print("To be developed")
    pass


def export_wn_synsets(args):
    if args.source == 'gloss':
        export_gloss_synsets(args)
    else:
        export_wnsql_synsets(args)


def export_gloss_synsets(args):
    print("Exporting synsets' info (lemmas/defs/examples) from GlossWordNet to text file")
    show_info(args)
    output_with_sid_file = os.path.abspath('./data/glosstag_lemmas.txt')
    output_without_sid_file = os.path.abspath('./data/glosstag_lemmas_noss.txt')
    output_defs = os.path.abspath('./data/glosstag_defs.txt')
    output_exes = os.path.abspath('./data/glosstag_exes.txt')
    gwn = get_gwn(args)
    # Extract lemmas
    wn_ss = gwn.schema.term.select()
    with open(output_with_sid_file, 'w') as with_sid, open(output_without_sid_file, 'w') as without_sid:
        for s in wn_ss:
            with_sid.write('%s\t%s\n' % (SynsetID.from_string(str(s.sid)), s.term))
            without_sid.write('%s\n' % (s.term,))
    # This table is not very helpful, definitions and examples are combined into a single string
    glosses = gwn.schema.gloss_raw.select(where='cat=?', values=('orig',))
    print(glosses[:5])
    return
    # Extract synset definitions
    defs = wn.schema.ss.select(orderby='synsetid')
    with open(output_defs, 'w') as def_file:
        for d in defs:
            def_file.write('{sid}\t{d}\n'.format(sid=SynsetID.from_string(d.synsetid), d=d.definition))
    # Extract examples
    exes = wn.schema.ex.select(orderby='synsetid')
    with open(output_exes, 'w') as ex_file:
        for ex in exes:
            ex_file.write('{sid}\t{ex}\n'.format(sid=SynsetID.from_string(ex.synsetid), ex=ex.sample))
    # summary
    print("Data has been extracted to:")
    print("  + {}".format(output_with_sid_file))
    print("  + {}".format(output_without_sid_file))
    print("  + {}".format(output_defs))
    print("  + {}".format(output_exes))
    print("Done!")
    

def export_wnsql_synsets(args):
    print("Exporting synsets' info (lemmas/defs/examples) from WordNetSQL to text file")
    show_info(args)
    output_with_sid_file = os.path.abspath('./data/wn30_lemmas.txt')
    output_without_sid_file = os.path.abspath('./data/wn30_lemmas_noss.txt')
    output_defs = os.path.abspath('./data/wn30_defs.txt')
    output_exes = os.path.abspath('./data/wn30_exes.txt')
    wn = get_wn(args)
    # Extract lemmas
    wn_ss = wn.get_all_synsets()
    with open(output_with_sid_file, 'w') as with_sid, open(output_without_sid_file, 'w') as without_sid:
        for s in wn_ss:
            with_sid.write('%s\t%s\n' % (SynsetID.from_string(str(s.synsetid)), s.lemma))
            without_sid.write('%s\n' % (s.lemma,))
    # Extract synset definitions
    defs = wn.schema.ss.select(orderby='synsetid')
    with open(output_defs, 'w') as def_file:
        for d in defs:
            def_file.write('{sid}\t{d}\n'.format(sid=SynsetID.from_string(d.synsetid), d=d.definition))
    # Extract examples
    exes = wn.schema.ex.select(orderby='synsetid')
    with open(output_exes, 'w') as ex_file:
        for ex in exes:
            ex_file.write('{sid}\t{ex}\n'.format(sid=SynsetID.from_string(ex.synsetid), ex=ex.sample))
    # summary
    print("Data has been extracted to:")
    print("  + {}".format(output_with_sid_file))
    print("  + {}".format(output_without_sid_file))
    print("  + {}".format(output_defs))
    print("  + {}".format(output_exes))
    print("Done!")


def show_info(args):
    print("GlossWordNet XML folder: %s" % args.gloss_xml)
    print("GlossWordNet SQlite DB : %s" % args.glossdb)
    print("Princeton WordNetSQL DB: %s" % args.wnsql)
    print("Use mockup data      : %s" % args.mockup)


def config_logging(args):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)

#----------------------------------------------------------------------


def main():
    '''Main entry

    '''
    # It's easier to create a user-friendly console application by using argparse
    # See reference at the top of this script
    parser = argparse.ArgumentParser(description="WordNet Toolkit - For accessing and manipulating WordNet")

    parser.add_argument('-i', '--gloss_xml', help='Path to Gloss WordNet folder (default = )', default=YLConfig.WORDNET_30_GLOSSTAG_PATH)
    parser.add_argument('-w', '--wnsql', help='Path to WordNet SQLite 3.0 database', default=YLConfig.WORDNET_30_PATH)
    parser.add_argument('-g', '--glossdb', help='Path to Gloss WordNet SQLite database', default=YLConfig.WORDNET_30_GLOSS_DB_PATH)
    parser.add_argument('-m', '--mockup', help='Use mockup data in dev_mode', action='store_true')

    tasks = parser.add_subparsers(title='task', help='Task to be performed')

    cmd_glosstag2ntumc = tasks.add_parser('g2n', help='Export Glosstag data to NTU-MC')
    cmd_glosstag2ntumc.set_defaults(func=glosstag2ntumc)

    cmd_extract = tasks.add_parser('extract', help='Extract XML synsets from glosstag')
    cmd_extract.add_argument('-s', '--source', required=False, help='Which Wordnet to be used (wnsql, gloss, etc.)')
    cmd_extract.set_defaults(func=export_wn_synsets)

    cmd_extract = tasks.add_parser('info', help='Show configuration information')
    cmd_extract.set_defaults(func=show_info)

    # Optional argument(s)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")

    # Parse input arguments
    if len(sys.argv) > 1:
        args = parser.parse_args()
        config_logging(args)
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
