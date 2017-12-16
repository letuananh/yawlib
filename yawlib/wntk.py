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
__copyright__ = "Copyright 2016, yawlib"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

import os.path
import logging

from chirptext.leutile import Timer, header, FileHelper
from chirptext.cli import CLIApp

from .helpers import add_wordnet_config
from .helpers import show_info
from .helpers import get_gwn, get_gwnxml
from .helpers import get_synset_by_id, get_synset_by_sk, get_synsets_by_term

# -----------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------
# >>> WARNING: Do NOT change these values here. Change config.py instead!
#
GLOSSTAG_NTUMC_OUTPUT = FileHelper.abspath('data/glosstag_ntumc')
GLOSSTAG_PATCH = FileHelper.abspath('data/glosstag_patch.xml')
MISALIGNED = FileHelper.abspath('data/misaligned.xml')


def get_logger():
    return logging.getLogger(__name__)


# -----------------------------------------------------------------------

def convert(cli, args):
    ''' Convert Gloss WordNet XML into SQLite format
    '''
    show_info(cli, args)

    if os.path.isfile(args.glossdb) and os.path.getsize(args.glossdb) > 0:
        print("DB file exists (%s | size: %s)" % (args.glossdb, os.path.getsize(args.glossdb)))
        answer = input("If you want to overwrite this file, please type CONFIRM: ")
        if answer != "CONFIRM":
            print("Script aborted!")
            exit()
    db = get_gwn(args)
    header('Importing data from XML to SQLite')
    t = Timer()
    header("Extracting Gloss WordNet (XML)")
    xmlgwn = get_gwnxml(args)
    header("Inserting data into SQLite database")
    t.start()
    db.insert_synsets(xmlgwn.synsets)
    t.end('Insertion completed.')
    pass


def search_by_id(cli, args):
    ''' Retrieve synset information by synsetid '''
    gwn = get_gwn(args)
    get_synset_by_id(gwn, args.synsetid, compact=not args.detail)


def search_by_key(cli, args):
    ''' Retrieve synset information by sensekey'''
    gwn = get_gwn(args)
    get_synset_by_sk(gwn, args.sensekey, compact=not args.detail)
    pass


def search_by_lemma(cli, args):
    ''' Retrieve synset information by lemma (term)'''
    gwn = get_gwn(args)
    get_synsets_by_term(gwn, args.lemma, args.pos, compact=not args.detail)
    pass


##############################################################
# MAIN
##############################################################

def main():
    '''Wordnet toolkit - CLI main() '''
    app = CLIApp(desc="WordNet Toolkit - For accessing and manipulating WordNet", logger=__name__)
    add_wordnet_config(app.parser)
    # Convert GWordnetXML into GWordnetSQL
    task = app.add_task('create', func=convert)
    # Search synsets by synsetID
    task = app.add_task('synset', func=search_by_id)
    task.add_argument('synsetid', help='Synset ID (e.g. 12345678-n)')
    task.add_argument('-d', '--detail', help='Display all gloss information (for debugging?)', action='store_true')
    # by sensekey
    task = app.add_task('key', func=search_by_key)
    task.add_argument('sensekey', help='sensekey (e.g. )')
    task.add_argument('-d', '--detail', help='Display all gloss information (for debugging?)', action='store_true')
    # by lemma (term)
    task = app.add_task('lemma', func=search_by_lemma)
    task.add_argument('lemma', help='lemma (term, word form, etc.)')
    task.add_argument('pos', nargs='?', help='Part-of-speech (a, n, r, x)')
    task.add_argument('-d', '--detail', help='Display all gloss information (for debugging?)', action='store_true')
    # show info
    task = app.add_task('info', func=show_info)
    # run app
    app.run()


if __name__ == "__main__":
    main()
