#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Useful functions for working with synsets
Latest version can be found at https://github.com/letuananh/yawlib

Usage:

    [TODO] WIP

Adapted from: https://github.com/letuananh/lelesk

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

import os.path
import itertools
import argparse
import logging
from collections import defaultdict as dd
from collections import namedtuple

from puchikarui import Schema, Execution#, DataSource, Table
from chirptext.leutile import StringTool, Counter, Timer, uniquify, header, jilog, TextReport, FileTool

from .models import SynsetID
from .config import YLConfig
from .glosswordnet import XMLGWordNet as GWNXML
from .glosswordnet import SQLiteGWordNet as GWNSQL
from .wordnetsql import WordNetSQL as WSQL

########################################################################
# CONFIGURATION
########################################################################

MOCKUP_SYNSETS_DATA = (FileTool.abspath('data/test.xml'),)

########################################################################


def get_synset_by_id(gwn, synsetid_str, report_file=None, compact=True):
    ''' Search synset in WordNet Gloss Corpus by synset ID'''
    if report_file is None:
        report_file = TextReport()  # Default to stdout
    report_file.print("Looking for synsets by synsetid (Provided: %s)\n" % synsetid_str)

    # Get synset infro from GlossWordnet
    try:
        synsetid = SynsetID.from_string(synsetid_str)
        synset = gwn.get_synset_by_id(synsetid.to_gwnsql())
        dump_synset(synset, report_file=report_file, compact=compact)
        return synset
    except Exception as e:
        print("    >>>> Error: {} (Synset ID should be in this format 12345678-n)".format(e))


def get_synset_by_sk(gwn, sk, report_file=None, compact=True):
    ''' Search synset in WordNet Gloss Corpus by sensekey'''
    if report_file is None:
        report_file = TextReport()  # Default to stdout
    report_file.print("Looking for synsets by sensekey (Provided: %s)\n" % sk)

    synset = gwn.get_synset_by_sk(sk)
    dump_synset(synset, report_file=report_file, compact=compact)
    return synset


def get_synsets_by_term(gwn, t, pos, report_file=None, compact=True):
    ''' Search synset in WordNet Gloss Corpus by term'''
    if report_file is None:
        report_file = TextReport()  # Default to stdout
    report_file.print("Looking for synsets by term (Provided: %s | pos = %s)\n" % (t, pos))

    synsets = gwn.get_synsets_by_term(t, pos)
    dump_synsets(synsets, report_file, compact=compact)

##################################################################


def dump_synsets(synsets, report_file=None, compact=True):
    ''' Dump a SynsetCollection to stdout

    Arguments:
        synsets     -- List of synsets to dump
        report_file -- An instance of TextReport
    '''
    if report_file is None:
        report_file = TextReport()  # Default to stdout

    if synsets:
        for synset in synsets:
            dump_synset(synset, report_file=report_file, compact=compact)
        report_file.print("Found %s synset(s)" % synsets.count())
    else:
        report_file.print("None was found!")


def dump_synset(ss, compact_gloss=False, compact_tags=False, more_compact=True, report_file=None, compact=True):
    ''' Print synset details for debugging purpose

    Arguments:
        ss            -- Synset object to dump
        compact_gloss -- Don't dump gloss tokens' details
        compact_tags  -- Don't dump tagged senses' details
        more_compact  -- Don't dump full details of synset
        report_file   -- Report file to write to

    '''
    if report_file is None:
        report_file = TextReport()  # Default to stdout

    if more_compact:
        report_file.header("Synset: %s (terms=%s | keys=%s)" % (ss.sid.to_canonical(), ss.terms, ss.keys), 'h0')
    else:
        report_file.header("Synset: %s" % ss, 'h0')

    for rgloss in ss.raw_glosses:
        if more_compact:
            if rgloss.cat != 'orig':
                continue
        report_file.print(rgloss)

    gloss_count = itertools.count(1)
    for gloss in ss.glosses:
        if compact:
            report_file.print("({cat}) {txt}".format(cat=gloss.cat, txt=gloss.text()))
        else:
            report_file.print('')
            report_file.header("Gloss #%s: %s" % (next(gloss_count), gloss), 'h2')

            # Dump gloss items
            if compact_gloss:
                report_file.print("Tokens => %s" % gloss.get_gramwords(), level=2)
            else:
                for item in gloss.items:
                    # print("\t%s - { %s }" % (uniquify(item.get_gramwords()), item))
                    report_file.print("%s - { %s }" % (set(item.get_gramwords()), item), level=2)
                report_file.print(("-" * 10), level=1)
            # Dump tags
            if compact_tags:
                report_file.print("Tags => %s" % gloss.get_tagged_sensekey(), level=2)
            else:
                for tag in gloss.tags:
                    report_file.print("%s" % tag, level=1)
    report_file.print('')

#############################################################
# argparse enhancement
#############################################################


def glosstag_files(merged_folder):
    return [os.path.join(merged_folder, 'adv.xml'),
            os.path.join(merged_folder, 'adj.xml'),
            os.path.join(merged_folder, 'verb.xml'),
            os.path.join(merged_folder, 'noun.xml')]


def get_gwnxml(args):
    if args.mockup:
        return GWNXML(args.mockup_files)
    else:
        merged_folder = os.path.join(args.gloss_xml, 'merged')
        gwn_xml = GWNXML(glosstag_files(merged_folder))
        return gwn_xml


def get_gwn(args):
    gwn = GWNSQL(args.glossdb)
    return gwn


def get_wn(args):
    wn = WSQL(args.wnsql)
    return wn


def config_logging(args):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)


def add_logging_config(parser):
    # Optional argument(s)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")


def add_wordnet_config(parser):
    '''Where to find different wordnets data'''
    parser.add_argument('-i', '--gloss_xml', help='Path to Gloss WordNet folder (default = )', default=YLConfig.WORDNET_30_GLOSSTAG_PATH)
    parser.add_argument('-w', '--wnsql', help='Path to WordNet SQLite 3.0 database', default=YLConfig.WORDNET_30_PATH)
    parser.add_argument('-g', '--glossdb', help='Path to Gloss WordNet SQLite database', default=YLConfig.WORDNET_30_GLOSS_DB_PATH)
    parser.add_argument('-m', '--mockup', help='Use mockup data in dev_mode', action='store_true')
    parser.set_defaults(mockup_files=MOCKUP_SYNSETS_DATA)


def show_info(args):
    ''' Show configuration information
    '''
    print("GlossWordNet XML folder: %s" % args.gloss_xml)
    print("GlossWordNet SQlite DB : %s" % args.glossdb)
    print("Princeton WordNetSQL DB: %s" % args.wnsql)
    print("Use mockup data      : %s" % args.mockup)


#--------------------------------------------------------

def main():
    jilog("This is a library, not a tool")


if __name__ == "__main__":
    main()
