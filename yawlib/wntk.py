#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAWLib console application

Usage:
    # Search sysets by term (word form) = `love' and POS is verb
    python3 wntk.py -t 'love' -p 'v'

    # Search synsets by synset-id
    python3 wntk.py -s 'v01775535'

    # Search synsets by sensekey
    python3 wntk.py -k 'love%2:37:01::'

    # Create SQLite database for searching
    python3 wntk.py -c -i ~/wordnet/glosstag -g ~/wordnet/gwn.db
"""

# This code is a part of yawlib library: https://github.com/letuananh/yawlib
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os.path
import logging

from texttaglib.chirptext.leutile import Timer, header, FileHelper
from texttaglib.chirptext.cli import CLIApp, setup_logging

from .helpers import add_wordnet_config
from .helpers import show_info, _LXML_AVAILABLE
from .helpers import get_gwn, get_gwnxml, get_omw, get_wn
from .helpers import get_synset_by_id, get_synset_by_sk, get_synsets_by_term
from .helpers import smart_wn_search

# -----------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------
# >>> WARNING: Do NOT change these values here. Change config.py instead!
#
GLOSSTAG_NTUMC_OUTPUT = FileHelper.abspath('data/glosstag_ntumc')
GLOSSTAG_PATCH = FileHelper.abspath('data/glosstag_patch.xml')
MISALIGNED = FileHelper.abspath('data/misaligned.xml')

# WN profiles
PWN30 = 'pwn30'
GWN = 'gwn'
OMW = 'omw'


def get_logger():
    return logging.getLogger(__name__)


# -----------------------------------------------------------------------

def convert(cli, args):
    """ Convert Gloss WordNet XML into SQLite format
    """
    if not _LXML_AVAILABLE:
        print("WARNING: lxml library is required for parsing XML")
        exit()

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


def get_wn_profile(cli, args):
    cli.logger.info("Loading Wordnet profile: {}".format(args.wn))
    if args.wn == GWN:
        return get_gwn(args)
    elif args.wn == PWN30:
        return get_wn(args)
    elif args.wn == OMW:
        return get_omw(args)
    else:
        raise Exception("Wordnet profile {} is not supported".format(args.wn))


def search_by_id(cli, args):
    """ Retrieve synset information by synsetid """
    wn = get_wn_profile(cli, args)
    get_synset_by_id(wn, args.synsetid, compact=not args.detail, lang=args.lang)


def search_by_key(cli, args):
    """ Retrieve synset information by sensekey"""
    wn = get_wn_profile(cli, args)
    get_synset_by_sk(wn, args.sensekey, compact=not args.detail, lang=args.lang)
    pass


def search_by_lemma(cli, args):
    """ Retrieve synset information by lemma (term)"""
    wn = get_wn_profile(cli, args)
    get_synsets_by_term(wn, args.lemma, args.pos, compact=not args.detail, lang=args.lang)
    pass


def search_everywhere(cli, args):
    """ Search for lemma and definitions"""
    wn = get_wn_profile(cli, args)
    smart_wn_search(wn, args.query, args.pos, compact=not args.detail, lang=args.lang)
    pass


##############################################################
# MAIN
##############################################################

def main():
    """Wordnet toolkit - CLI main() """
    setup_logging('logging.json', 'logs')
    app = CLIApp(desc="WordNet Toolkit - For accessing and manipulating WordNet", logger=__name__)
    add_wordnet_config(app.parser)
    # Convert GWordnetXML into GWordnetSQL
    task = app.add_task('create', func=convert)
    # Search synsets by synsetID
    task = app.add_task('synset', func=search_by_id)
    task.add_argument('synsetid', help='Synset ID (e.g. 12345678-n)')
    task.add_argument('-d', '--detail', help='Display all gloss information (for debugging?)', action='store_true')
    task.add_argument('--wn', help='Which Wordnet to use', choices=[GWN, PWN30, OMW], default=GWN)
    task.add_argument('--lang', help='Search language', default='eng')
    # by sensekey
    task = app.add_task('key', func=search_by_key)
    task.add_argument('sensekey', help='sensekey (e.g. )')
    task.add_argument('-d', '--detail', help='Display all gloss information (for debugging?)', action='store_true')
    task.add_argument('--wn', help='Which Wordnet to use', choices=[GWN, PWN30, OMW], default=GWN)
    task.add_argument('--lang', help='Search language', default='eng')
    # by lemma (term)
    task = app.add_task('lemma', func=search_by_lemma)
    task.add_argument('lemma', help='lemma (term, word form, etc.)')
    task.add_argument('pos', nargs='?', help='Part-of-speech (a, n, r, x)')
    task.add_argument('-d', '--detail', help='Display all gloss information (for debugging?)', action='store_true')
    task.add_argument('--wn', help='Which Wordnet to use', choices=[GWN, PWN30, OMW], default=GWN)
    task.add_argument('--lang', help='Search language', default='eng')

    # search everywhere
    task = app.add_task('search', func=search_everywhere)
    task.add_argument('query', help='a query (term, word form, etc.) to search in lemmas and definitions')
    task.add_argument('pos', nargs='?', help='Part-of-speech (a, n, r, x)')
    task.add_argument('-d', '--detail', help='Display all gloss information (for debugging?)', action='store_true')
    task.add_argument('--wn', help='Which Wordnet to use', choices=[GWN, PWN30, OMW], default=GWN)
    task.add_argument('--lang', help='Search language', default='eng')

    # show info
    task = app.add_task('info', func=show_info)
    task.add_argument('-o', '--output', help='Write information to a text file')
    # run app
    app.run()


if __name__ == "__main__":
    main()
