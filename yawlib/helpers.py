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

from .models import SynsetID, SynsetCollection
from yawlib import YLConfig
from yawlib.glosswordnet.gwnmodels import GlossedSynset
from yawlib import GWordnetXML as GWNXML
from yawlib import GWordnetSQLite as GWNSQL
from yawlib import WordnetSQL as WSQL
from yawlib.common import InvalidSynsetID, WordnetFeatureNotSupported, SynsetNotFoundException
from yawlib.omwsql import OMWSQL

########################################################################
# CONFIGURATION
########################################################################

MOCKUP_SYNSETS_DATA = (FileHelper.abspath('data/test.xml'),)
logger = logging.getLogger()


def getLogger():
    return logging.getLogger(__name__)


########################################################################


def get_synset_by_id(wn, synsetid_str, report_file=None, compact=True, lang=None):
    ''' Search synset in WordNet Gloss Corpus by synset ID'''
    if report_file is None:
        report_file = TextReport()  # Default to stdout
    report_file.print("Looking for synsets by synsetid (Provided: %s)" % synsetid_str)

    # Get synset infro from GlossWordnet
    try:
        synsetid = SynsetID.from_string(synsetid_str)
        synset = wn.get_synset(synsetid, lang=lang)
        dump_synset(synset, report_file=report_file, compact=compact)
        return synset
    except InvalidSynsetID as e:
        getLogger().exception("Error occurred. (Synset ID should be in this format 12345678-n)")


def get_synset_by_sk(wn, sk, report_file=None, compact=True, lang=None):
    ''' Search synset in WordNet Gloss Corpus by sensekey'''
    if report_file is None:
        report_file = TextReport()  # Default to stdout
    report_file.print("Looking for synsets by sensekey (Provided: %s)" % sk)

    synset = wn.get_by_key(sk, lang=lang)
    dump_synset(synset, report_file=report_file, compact=compact)
    return synset


def get_synsets_by_term(wn, t, pos=None, report_file=None, compact=True, lang=None, with_eng=True):
    ''' Search synset in WordNet Gloss Corpus by term'''
    if report_file is None:
        report_file = TextReport()  # Default to stdout
    report_file.print("Looking for synsets by term (Provided: %s | pos = %s)" % (t, pos))

    with wn.ctx() as ctx:
        synsets = wn.search(t, pos, lang=lang, ctx=ctx)
        if with_eng and lang != 'eng':
            synsets_eng = SynsetCollection()
            for synset in synsets:
                synset_eng = wn.get_synset(synset.ID, lang='eng', ctx=ctx)
                synsets_eng.add(synset_eng)
            dump_synsets(synsets, synsets_eng, report_file=report_file, compact=compact)
        else:
            dump_synsets(synsets, report_file=report_file, compact=compact)

    return synsets


def smart_wn_search(wn, query, pos=None, report_file=None, compact=True, lang='eng', with_eng=True):
    ''' Search synset in WordNet Gloss Corpus by term'''
    if report_file is None:
        report_file = TextReport()  # Default to stdout
    report_file.print("Search Wordnet: Query=%s | POS=%s" % (query, pos))

    with wn.ctx() as ctx:
        synsets = search_wn_full_text(wn, query, pos=pos, lang=lang, ctx=ctx)
        if with_eng and lang != 'eng':
            synsets_eng = SynsetCollection()
            for synset in synsets:
                synset_eng = wn.get_synset(synset.ID, lang='eng', ctx=ctx)
                synsets_eng.add(synset_eng)
            dump_synsets(synsets, synsets_eng, report_file=report_file, compact=compact)
        else:
            dump_synsets(synsets, report_file=report_file, compact=compact)
    return synsets


def search_wn_full_text(wn, query, pos=None, lang='eng', auto_wrap=True, ctx=None):
    if ctx is None:
        with wn.ctx() as ctx:
            return search_wn_full_text(wn, query, pos=pos, lang=lang, auto_wrap=auto_wrap, ctx=ctx)
    # First, search by synset ID and POS
    try:
        synset = wn.get_synset(query, lang=lang, ctx=ctx)
        if synset:
            return SynsetCollection((synset,))
    except InvalidSynsetID:
        pass
    # else, search by sensekey
    try:
        synset = wn.get_by_key(query, lang=lang, ctx=ctx)
        if synset:
            return SynsetCollection((synset,))
    except (WordnetFeatureNotSupported, SynsetNotFoundException):
        pass
    # else, search by lemma or definition
    if auto_wrap and '%' not in query and '?' not in query:
        query = '%{}%'.format(query)
    # 1. by lemma
    synsets = wn.search(query, pos, lang=lang, ctx=ctx)
    # 2. in definitions
    wn.search_def(query, lang=lang, synsets=synsets, ctx=ctx)
    # 3. in examples
    wn.search_ex(query, lang=lang, synsets=synsets, ctx=ctx)
    return synsets

##################################################################


def dump_synsets(*synsets, report_file=None, compact=True):
    ''' Dump a SynsetCollection to stdout

    Arguments:
        *synsets     -- Lists of synsets to dump
        report_file -- An instance of TextReport
    '''
    if report_file is None:
        report_file = TextReport()  # Default to stdout

    synsets = [group for group in synsets if group]
    if len(synsets) > 0:
        main_group = synsets[0]
        for synset in main_group:
            synset_langs = [synset]
            synset_langs.extend(group[synset.ID] for group in synsets[1:] if synset.ID in group)
            dump_synset(*synset_langs, report_file=report_file, compact=compact)
        report_file.print("Found %s synset(s)" % main_group.count())
    else:
        report_file.print("None was found!")


def dump_synset(*synset_langs, compact_gloss=False, compact_tags=False, more_compact=True, report_file=None, compact=True):
    ''' Print synset details for debugging purpose

    Arguments:
        synset_langs  -- Synset objects (in different languages) to dump
        compact_gloss -- Don't dump gloss tokens' details
        compact_tags  -- Don't dump tagged senses' details
        more_compact  -- Don't dump full details of synset
        report_file   -- Report file to write to

    '''
    if report_file is None:
        report_file = TextReport()  # Default to stdout
    if synset_langs is None or len(synset_langs) == 0:
        getLogger().warning("No synset to dump")
        return

    ss_canon = synset_langs[0]
    ss_header = ["〔Synset〕{}".format(ss_canon.ID)]
    for synset in synset_langs:
        # only display language if we have more than 1 language
        if len(synset_langs) > 1 and synset.lang and (synset.lemmas or synset.sensekeys):
            ss_header.append("[{}]".format(synset.lang))
        if synset.lemmas:
            ss_header.append("〔Lemmas〕{}".format('; '.join(synset.lemmas)))
        if synset.sensekeys:
            ss_header.append("〔Keys〕{}".format(' '.join(synset.sensekeys)))
    report_file.header(" ".join(ss_header), level='h1')

    if isinstance(synset, GlossedSynset):
        for synset in synset_langs:
            # only display language if we have more than 1 language
            if len(synset_langs) > 1 and synset.lang:
                report_file.print("[{}]".format(synset.lang))
            if not more_compact:
                for rgloss in synset.raw_glosses:
                    if compact:
                        if rgloss.cat != 'orig':
                            continue
                    report_file.print(rgloss)
            gloss_count = itertools.count(1)
            for gloss in synset.glosses:
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
    else:
        # print def, exs
        # only display language if we have more than 1 language
        prefix = ""
        for synset in synset_langs:
            if len(synset_langs) > 1 and synset.lang:
                prefix = "[{}]".format(synset.lang)
            if synset.definition:
                report_file.print("{}(def) {}".format(prefix, synset.definition))
        for synset in synset_langs:
            if len(synset_langs) > 1 and synset.lang:
                prefix = "[{}]".format(synset.lang)
            if synset.examples:
                for ex in synset.examples:
                    report_file.print("{}(ex) {}".format(prefix, ex))
                    prefix = ' ' * len(prefix)
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
