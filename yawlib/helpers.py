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
import itertools
import logging

from chirptext.leutile import TextReport, FileHelper

from .models import SynsetID
from yawlib import YLConfig
from yawlib import GWordnetXML as GWNXML
from yawlib import GWordnetSQLite as GWNSQL
from yawlib import WordnetSQL as WSQL
from yawlib.omwsql import OMWSQL

########################################################################
# CONFIGURATION
########################################################################

MOCKUP_SYNSETS_DATA = (FileHelper.abspath('data/test.xml'),)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

########################################################################


def get_synset_by_id(gwn, synsetid_str, report_file=None, compact=True):
    ''' Search synset in WordNet Gloss Corpus by synset ID'''
    if report_file is None:
        report_file = TextReport()  # Default to stdout
    report_file.print("Looking for synsets by synsetid (Provided: %s)" % synsetid_str)

    # Get synset infro from GlossWordnet
    try:
        synsetid = SynsetID.from_string(synsetid_str)
        synset = gwn.get_synset(synsetid.to_gwnsql())
        dump_synset(synset, report_file=report_file, compact=compact)
        return synset
    except Exception as e:
        logger.exception(e)
        logger.error("  >>>> Error: (Synset ID should be in this format 12345678-n)")


def get_synset_by_sk(gwn, sk, report_file=None, compact=True):
    ''' Search synset in WordNet Gloss Corpus by sensekey'''
    if report_file is None:
        report_file = TextReport()  # Default to stdout
    report_file.print("Looking for synsets by sensekey (Provided: %s)" % sk)

    synset = gwn.get_by_key(sk)
    dump_synset(synset, report_file=report_file, compact=compact)
    return synset


def get_synsets_by_term(gwn, t, pos=None, report_file=None, compact=True):
    ''' Search synset in WordNet Gloss Corpus by term'''
    if report_file is None:
        report_file = TextReport()  # Default to stdout
    report_file.print("Looking for synsets by term (Provided: %s | pos = %s)" % (t, pos))

    synsets = gwn.search(t, pos)
    dump_synsets(synsets, report_file, compact=compact)
    return synsets

##################################################################


def dump_synsets(synsets, report_file=None, compact=True):
    ''' Dump a SynsetCollection to stdout

    Arguments:
        synsets     -- List of synsets to dump
        report_file -- An instance of TextReport
    '''
    if report_file is None:
        report_file = TextReport()  # Default to stdout

    if synsets is not None:
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
        report_file.header("〔Synset〕 %s 〔Lemmas〕%s 〔Keys〕%s" % (ss.ID, '; '.join(ss.lemmas), ' '.join(ss.sensekeys)), level='h1')
    else:
        report_file.header("Synset: %s" % ss, level='h0')

    if not more_compact:
        for rgloss in ss.raw_glosses:
            if compact:
                if rgloss.cat != 'orig':
                    continue
            report_file.print(rgloss)

    gloss_count = itertools.count(1)
    for gloss in ss.glosses:
        if compact:
            txt = gloss.text() if gloss.cat != 'def' else '“{}”'.format(gloss.text())
            report_file.print("({cat}) {txt}".format(cat=gloss.cat, txt=txt))
        else:
            report_file.print('')
            report_file.header("Gloss #%s: %s" % (next(gloss_count), gloss), level='h2')

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


def get_gwn(args=None):
    gdb = args.glossdb if args else YLConfig.GWN30_DB
    gwn = GWNSQL(gdb)
    return gwn


def get_wn(args=None):
    wnsql = args.wnsql if args else YLConfig.WNSQL30_PATH
    wn = WSQL(wnsql)
    return wn


def get_omw(args=None):
    db_path = args.omw if args is not None and args.omw else YLConfig.OMW_DB
    return OMWSQL(db_path)


def add_wordnet_config(parser):
    '''Where to find different wordnets data'''
    parser.add_argument('-i', '--gloss_xml', help='Path to Gloss WordNet folder', default=YLConfig.GWN30_PATH)
    parser.add_argument('-w', '--wnsql', help='Path to WordNet SQLite 3.0 DB', default=YLConfig.WNSQL30_PATH)
    parser.add_argument('-g', '--glossdb', help='Path to Gloss WordNet SQLite DB', default=YLConfig.GWN30_DB)
    parser.add_argument('-o', '--omw', help='Path to Open Multilingual WordNet SQLite DB', default=YLConfig.OMW_DB)
    parser.add_argument('-m', '--mockup', help='Use mockup data in dev_mode', action='store_true')
    parser.set_defaults(mockup_files=MOCKUP_SYNSETS_DATA)


def show_info(cli, args):
    ''' Show configuration information
    '''
    print("GlossWordNet XML folder: %s" % args.gloss_xml)
    print("GlossWordNet SQlite DB : %s" % args.glossdb)
    print("Princeton WordnetSQL DB: %s" % args.wnsql)
    print("OMW DB                 : %s" % args.omw)
    print("Use mockup data        : %s" % args.mockup)
    if args.verbose:
        print("--verbose              : %s" % args.verbose)
    if args.quiet:
        print("--quiet                : %s" % args.quiet)
