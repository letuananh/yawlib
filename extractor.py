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

# import sys
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

def get_gwn(gwn_db_loc=WORDNET_30_GLOSS_DB_PATH):
    gwn = SQLiteGWordNet(gwn_db_loc)
    return gwn

def get_wn(wn_db_loc=WORDNET_30_PATH):
    wn = WSQL(wn_db_loc)
    return wn

def dev_mode(gwn_db_loc, wn_db_loc, mockup):
    print("GlossWordNet location: %s" % gwn_db_loc)
    print("WordNet location     : %s" % wn_db_loc)
    print("Use mockup data      : %s" % mockup)
    gwn = get_gwn(gwn_db_loc)
    wn = get_wn(wn_db_loc)

#-----------------------------------------------------------------------

def main():
    '''Main entry

    '''
    # It's easier to create a user-friendly console application by using argparse
    # See reference at the top of this script
    parser = argparse.ArgumentParser(description="WordNet Toolkit - For accessing and manipulating WordNet")
    
    # Positional argument(s)
    # parser.add_argument('task', help='Task to perform (create/import/synset)')

    parser.add_argument('-i', '--gwn_location', help='Path to Gloss WordNet folder (default = ~/wordnet/glosstag')
    parser.add_argument('-o', '--gwn_db', help='Path to database file (default = ~/wordnet/glosstag.db')
    parser.add_argument('-w', '--wnsql', help='Location to WordNet SQLite 3.0 database')
    parser.add_argument('-g', '--glosswn', help='Location to Gloss WordNet SQLite database')

    parser.add_argument('-m', '--mockup', help='Use mockup data in dev_mode', action='store_true')
    parser.add_argument('-n', '--ntumc', help='Extract GlossWordNet to NTU-MC', action='store_true')
    parser.add_argument('-d', '--dev', help='Dev mode (do not use)', action='store_true')
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

    wng_loc = args.gwn_location if args.gwn_location else WORDNET_30_GLOSSTAG_PATH
    gwn_db_loc = args.gwn_db if args.gwn_db else (args.glosswn if args.glosswn else WORDNET_30_GLOSS_DB_PATH)
    wn_db_loc = args.wnsql if args.wnsql else WORDNET_30_PATH

    # Now do something ...
    if args.dev:
        dev_mode(gwn_db_loc, wn_db_loc, args.mockup)
    elif args.extract:
        extract_synsets_xml()
    elif args.ntumc:
        export_ntumc(wng_loc, gwn_db_loc, args.mockup)
    else:
        parser.print_help()
    pass # end main()

if __name__ == "__main__":
    main()
