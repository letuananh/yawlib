#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Extract information from several wordnet formats
Latest version can be found at https://github.com/letuananh/yawlib

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

import sys
import os.path
import argparse
import itertools
import logging
import csv
from collections import defaultdict as dd
from collections import namedtuple
from difflib import ndiff, unified_diff
from operator import itemgetter

from lxml import etree
from fuzzywuzzy import fuzz

from chirptext.leutile import StringTool
from chirptext.leutile import Counter
from chirptext.leutile import Timer
from chirptext.leutile import uniquify
from chirptext.leutile import header
from chirptext.leutile import FileHelper

from yawlib import YLConfig
from yawlib import SynsetID
from yawlib.helpers import dump_synset
from yawlib.helpers import dump_synsets
from yawlib.helpers import get_gwn, get_wn, get_gwnxml
from yawlib.helpers import config_logging, add_logging_config
from yawlib.helpers import add_wordnet_config
from yawlib.helpers import show_info
from yawlib import XMLGWordNet
from yawlib import SQLiteGWordNet
from yawlib import WordnetSQL as WSQL

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
MOCKUP_SYNSETS_DATA      = FileHelper.abspath('data/test.xml')
GLOSSTAG_NTUMC_OUTPUT    = FileHelper.abspath('data/glosstag_ntumc')
GLOSSTAG_PATCH           = FileHelper.abspath('data/glosstag_patch.xml')
glosstag_files = lambda x : [
    os.path.join(x, 'adv.xml')
    ,os.path.join(x, 'adj.xml')
    ,os.path.join(x, 'verb.xml')
    ,os.path.join(x, 'noun.xml')
    ]
MERGED_FOLDER            = os.path.join(WORDNET_30_GLOSSTAG_PATH , 'merged')
GLOSSTAG_XML_FILES       = glosstag_files(MERGED_FOLDER)
MISALIGNED               = FileHelper.abspath('data/misaligned.xml')

#-----------------------------------------------------------------------


def glosstag2ntumc(args):
    print("Extracting Glosstag to NTU-MC")
    show_info(args)
    print("To be developed")
    pass


def export_wn_synsets(args):
    '''Extract information from different wordnets to compare'''
    if args.source == 'gloss':
        export_gwnsql_synsets(args)
    else:
        export_wnsql_synsets(args)


def export_gwnsql_synsets(args):
    print("Exporting synsets' info (lemmas/defs/examples) from GlossWordNet (SQLite) to text file")
    show_info(args)
    output_with_sid_file = os.path.abspath('./data/glosstag_lemmas.txt')
    output_without_sid_file = os.path.abspath('./data/glosstag_lemmas_noss.txt')
    output_defs = os.path.abspath('./data/glosstag_defs.txt')
    output_exes = os.path.abspath('./data/glosstag_exes.txt')
    gwn = get_gwn(args)

    # Extract synsets' lemmas, definitions and examples
    if args.mockup:
        synsets = get_gwnxml(args).synsets
    else:
        synsets = gwn.all_synsets()

    synsets.synsets.sort(key=lambda x: x.sid.to_canonical())
    with open(output_defs, 'w') as def_file, open(output_exes, 'w') as ex_file, open(output_with_sid_file, 'w') as with_sid, open(output_without_sid_file, 'w') as without_sid:
        # synsets = gwn.get_synsets_by_ids(['01828736-v', '00001740-r'])
        for ss in synsets:
            for t in sorted(ss.terms, key=lambda x: x.term):
                with_sid.write('%s\t%s\n' % (ss.sid.to_canonical(), t.term))
                without_sid.write('%s\n' % (t.term,))
            for gloss in ss.glosses:
                if gloss.cat == 'def':
                    def_file.write('{sid}\t{d}\n'.format(sid=ss.sid, d=gloss.text()))
                elif gloss.cat == 'ex':
                    ex_file.write('{sid}\t{ex}\n'.format(sid=ss.sid, ex=gloss.text()))
    # summary
    print("Data has been extracted to:")
    print("  + {}".format(output_with_sid_file))
    print("  + {}".format(output_without_sid_file))
    print("  + {}".format(output_defs))
    print("  + {}".format(output_exes))
    print("Extracted synsets: {}".format(len(synsets)))
    print("Done!")


def export_wnsql_synsets(args):
    print("Exporting synsets' info (lemmas/defs/examples) from WordnetSQL (Princeton Wordnet 3.0) to text file")
    show_info(args)
    output_with_sid_file = os.path.abspath('./data/wn30_lemmas.txt')
    output_without_sid_file = os.path.abspath('./data/wn30_lemmas_noss.txt')
    output_defs = os.path.abspath('./data/wn30_defs.txt')
    output_exes = os.path.abspath('./data/wn30_exes.txt')
    wn = get_wn(args)
    # Extract lemmas
    records = wn.get_all_synsets()
    synsets_lemmas = []
    for r in records:
        synsets_lemmas.append((SynsetID.from_string(str(r.synsetid)).to_canonical(), r.lemma))
    synsets_lemmas.sort(key=itemgetter(0, 1))
    with open(output_with_sid_file, 'w') as with_sid, open(output_without_sid_file, 'w') as without_sid:
        for row in synsets_lemmas:
            with_sid.write('%s\t%s\n' % row)
            without_sid.write('%s\n' % (row[1],))  # just the lemma

    # Extract synset definitions
    records = wn.schema.ss.select(orderby='synsetid')
    synsets_defs = []
    for r in records:
        synsets_defs.append((SynsetID.from_string(r.synsetid).to_canonical(), r.definition))
    synsets_defs.sort(key=itemgetter(0))
    with open(output_defs, 'w') as def_file:
        for row in synsets_defs:
            def_file.write('%s\t%s\n' % row)

    # Extract examples
    records = wn.schema.ex.select(orderby='synsetid')
    synsets_examples = []
    for r in records:
        synsets_examples.append((SynsetID.from_string(r.synsetid).to_canonical(), r.sample))
    synsets_examples.sort(key=itemgetter(0))
    with open(output_exes, 'w') as ex_file:
        for row in synsets_examples:
            ex_file.write('%s\t%s\n' % row)

    # summary
    print("Data has been extracted to:")
    print("  + {}".format(output_with_sid_file))
    print("  + {}".format(output_without_sid_file))
    print("  + {}".format(output_defs))
    print("  + {}".format(output_exes))
    print("Done!")


# wordnet data
class WNData:
    def __init__(self, profile, folder='./data/'):
        self.profile = profile
        self.lemmas_file = os.path.join(folder, '{}_lemmas.txt'.format(profile))
        self.defs_file = os.path.join(folder, '{}_defs.txt'.format(profile))
        self.exes_file = os.path.join(folder, '{}_exes.txt'.format(profile))
        self.sids = set()
        self.lemma_map = dd(set)
        self.lemmas = []
        self.def_map = {}
        self.defs = []
        self.exes = []

    def read(self):
        self.read_lemmas()
        self.read_defs()
        return self

    def read_lemmas(self):
        print("Reading file: {}".format(self.lemmas_file))
        with open(self.lemmas_file) as lmfile:
            self.lemmas = list(csv.reader(lmfile, dialect='excel-tab'))
            for sid, lemma in self.lemmas:
                self.sids.add(sid)
                # self.lemma_map[sid].add(lemma)
                self.lemma_map[sid].add(lemma.lower())
            print("Lemma count: {}".format(len(self.lemmas)))
            print("Synset count: {}".format(len(self.lemma_map)))

    def fix_def(self, definition):
        if definition.endswith(';'):
            definition = definition[:-1]
        definition = definition.replace('( ', '(').replace(' )', ')').replace(' , ', ', ')
        return definition

    def read_defs(self):
        print("Reading file: {}".format(self.defs_file))
        with open(self.defs_file) as deffile:
            self.defs = list(csv.reader(deffile, dialect='excel-tab'))
            for sid, definition in self.defs:
                if sid in self.def_map:
                    print("WARNING: multiple definition found for {}".format(sid))
                self.def_map[sid] = self.fix_def(definition)
        print("Def count: {}".format(len(self.defs)))

    def get_sid(self, sid):
        if sid not in self.sids:
            if sid.endswith('r'):
                trysid = sid[:-1] + 's'
            elif sid.endswith('s'):
                trysid = sid[:-1] + 'r'
            if trysid in self.sids:
                return trysid
        else:
            return sid
        return None

    def compare_to(self, other_wn):
        c = Counter()
        for sid in self.sids:
            other_sid = sid
            if sid not in other_wn.lemma_map:
                if sid.endswith('r'):
                    # inconsistent convention (-r = -s)
                    other_sid = sid[:-2] + '-s'
                    if other_sid not in other_wn.sids:
                        print("sid {sid} cannot be found in [{prof}]".format(sid=sid, prof=other_wn.profile))
                        c.count("synset diff")
                        continue
            # we found this sid ...
            if self.lemma_map[sid] != other_wn.lemma_map[other_sid]:
                c.count('Lemma diff')
                print("{}: [{}] vs [{}]".format(sid, self.lemma_map[sid], other_wn.lemma_map[other_sid]))
        # compare defs
        diffs = set()  # store all differences to see 
        for sid in self.sids:
            other_sid = other_wn.get_sid(sid)
            if not other_sid:
                print("Cannot find definition for {}".format(sid))
            mydef = self.def_map[sid]
            odef = other_wn.def_map[other_sid]
            if fuzz.ratio(mydef, odef) < 100:
                diff = simple_diff(mydef, odef)
                if ''.join(set(diff)) not in '(-_ \'";.':
                    diffs.add(diff)
                    c.count("def diff")
                    print("{prof} ({sid}): {mydef}\n{otherprof} ({osid}): {otherdef}\ndiff: {diff}--".format(prof=self.profile, sid=sid, mydef=mydef, otherprof=other_wn.profile, osid=other_sid, otherdef=odef, diff=diff))
            else:
                c.count("def same")
        print('-' * 30)
        with open(os.path.abspath('./data/diffs.txt'), 'w') as outfile:
            outfile.write('\n'.join(diffs))
        print('\n'.join(sorted(diffs)))
        c.summarise()


def simple_diff(a, b):
    '''Extract the difference between two strings'''
    diffs = unified_diff(a, b)
    parts = []
    for d in [x for x in diffs if x[0] in '-+?' and x.strip() not in ['---', '+++']]:
        parts.append(d[1:].strip())
    return ''.join(parts)


def compare_wordnets(args):
    gwn = WNData('glosstag').read()
    wn30 = WNData('wn30').read()
    # compare wordnets
    gwn.compare_to(wn30)


# ----------------------------------------------------------------------

def main():
    '''Main entry

    '''
    # It's easier to create a user-friendly console application by using argparse
    # See reference at the top of this script
    parser = argparse.ArgumentParser(description="WordNet Toolkit - For accessing and manipulating WordNet")
    add_wordnet_config(parser)
    add_logging_config(parser)

    tasks = parser.add_subparsers(title='task', help='Task to be performed')

    cmd_glosstag2ntumc = tasks.add_parser('g2n', help='Export Glosstag data to NTU-MC')
    cmd_glosstag2ntumc.set_defaults(func=glosstag2ntumc)

    cmd_extract = tasks.add_parser('x', help='Extract XML synsets from glosstag')
    cmd_extract.add_argument('source', nargs='?', help='Which Wordnet to be used (wnsql, gloss, etc.)')
    cmd_extract.set_defaults(func=export_wn_synsets)

    cmd_compare = tasks.add_parser('compare', help='Compare extracted wordnets')
    cmd_compare.set_defaults(func=compare_wordnets)

    cmd_info = tasks.add_parser('info', help='Show configuration information')
    cmd_info.set_defaults(func=show_info)

    # Parse input arguments
    if len(sys.argv) > 1:
        args = parser.parse_args()
        config_logging(args)
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
