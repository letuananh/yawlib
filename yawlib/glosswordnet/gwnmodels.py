#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gloss WordNet Data Transfer Object
"""

# This code is a part of yawlib library: https://github.com/letuananh/yawlib
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import logging
import re
from collections import defaultdict as dd

from yawlib.models import Synset
from texttaglib.chirptext.leutile import StringTool
from texttaglib.chirptext import ttl


# -----------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------

REMAIN_PATTERN = re.compile('[" ;]')


def getLogger():
    return logging.getLogger(__name__)


# -----------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------

class GlossedSynset(Synset):
    """ Each synset object comes with sensekeys (ref: SenseKey), terms (ref: Term), and 3 glosses (ref: GlossRaw).
    """

    def __init__(self, sid, keys=None, lemmas=None, defs=None, exes=None):
        super().__init__(sid, keys, lemmas, defs, exes)
        self.raw_glosses = []  # list of GlossRaw
        self.glosses = []      # list of Gloss

    @property
    def definition(self):
        """ Override Synset.definition """
        def_obj = self.get_def()
        return None if def_obj is None else def_obj.surface

    @property
    def examples(self):
        """ Override Synset.examples """
        return [ex.surface for ex in self.get_examples()]

    def get_def(self):
        for gloss in self.glosses:
            if gloss.cat == 'def':
                return gloss
        return None

    def get_examples(self):
        return [g for g in self.glosses if g.cat == 'ex']

    def get_domain(self):
        return [g for g in self.glosses if g.cat == 'classif']

    def get_aux(self):
        return [g for g in self.glosses if g.cat == 'aux']

    def add_raw_gloss(self, cat, gloss):
        gr = GlossRaw(self, cat, gloss)
        self.raw_glosses.append(gr)

    def add_gloss(self, origid, cat, gid=-1):
        g = Gloss(self, origid, cat, gid)
        self.glosses.append(g)
        return g

    def get_surface(self):
        orig = self.get_orig()
        return orig.gloss if orig is not None else ''

    def get_orig(self):
        """ Get orig gloss (aux + def + examples) """
        for gr in self.raw_glosses:
            if gr.cat == 'orig':
                return gr
        return None

    def get_gramwords(self, nopunc=True):
        words = []
        for gloss in self.glosses:
            words.extend(gloss.get_gramwords(nopunc))
        return words

    def get_tags(self):
        keys = []
        for gloss in self.glosses:
            keys.extend(gloss.get_tagged_sensekey())
        return keys

    def match_surface(self, raws=None):
        """ Match tokens in each gloss to original synset def+ex string """
        raws = self.get_orig().split() if raws is None else list(raws)
        glosses = list(self.glosses)  # remaining glosses
        logger = getLogger()
        try:
            # try to match normally first
            for r, g in zip(raws, glosses):
                tokens = [t.text for t in g]
                while tokens[-1] == ';':
                    tokens.pop()
                sent = ttl.Sentence(r)
                sent.tokens = tokens
            # seems ok ...
            for r, g in zip(raws, glosses):
                g.surface = r
            return True
        except:
            pass
        # split def raw if needed
        d = self.get_def()
        for idx, raw in enumerate(raws):
            sent = ttl.Sentence(raw)
            tokens = [i.text for i in d.items]
            try:
                sent.tokens = tokens
                # found the def raw
                if "(" in raw:
                    new_part = raw.replace("(", ";(").split(";")
                    raws[idx] = new_part[0]
                    for loc, part in enumerate(new_part[1:]):
                        raws.insert(idx + loc + 1, part)
                    break
            except:
                continue
        while len(raws) > 0:
            raw = raws.pop()
            for idx, g in enumerate(glosses):
                s = ttl.Sentence(raw)
                tokens = [t.text for t in g.items]
                # logger.debug("raw = {} | tokens = {}".format(s.text, tokens))
                while tokens[-1] == ';':
                    tokens.pop()
                try:
                    s.import_tokens(tokens)
                    g.surface = raw
                    glosses.pop(idx)  # remove this gloss as it's matched
                    raw = None
                    break
                except:
                    # move on to the next one
                    # logger.exception("Failed to match: {} to {}".format(g.text(), tokens))
                    pass
            if raw:
                logger.warning("Could not match {} to anything | remaining glosses: {}".format(raw, [g.text() for g in glosses]))
        if len(glosses) > 0:
            raise Exception("mismatched! Remaining glosses: {} | orig: {}".format([g.text() for g in glosses], self.get_orig()))
        return True

    def __getitem__(self, name):
        return self.glosses[name]

    def __repr__(self):
        if self.lemmas is not None and len(self.lemmas) > 0:
            return "{sid} ({lemma})".format(sid=self.synsetid.to_canonical(), lemma=self.lemmas[0])
        else:
            return "(GSynset:{})".format(self.synsetid)

    def __str__(self):
        return repr(self)


class GlossRaw:
    """ Raw glosses extracted from WordNet Gloss Corpus.
        Each synset has a orig_gloss, a text_gloss and a wsd_gloss
    """

    # Categories
    ORIG = 'orig'
    TEXT = 'text'

    def __init__(self, synset, cat, gloss):
        self.synset = synset
        self.cat = StringTool.strip(cat)
        self.gloss = StringTool.strip(gloss)

    def __str__(self):
        return "[gloss-%s] %s" % (self.cat, self.gloss)

    def split(self):
        raws = self.gloss.split(';')
        if self.synset is None:
            return raws
        glosses = self.synset.glosses
        if len(glosses) == 1:
            # no need to split actually
            return [self.gloss]
        if glosses[0].cat == 'aux':
            # the first need to be split further ...
            laux = len(glosses[0].text())
            next_part = glosses[1]
            if len(next_part.items) > 0:
                cut = raws[0].find(next_part[0].text, laux)
                first = raws[0][:cut]
                second = raws[0][cut:]
                raws[0] = second
                raws.insert(0, first)
        # look for first definition part
        def_idx = 0
        for idx, g in enumerate(glosses):
            if g.cat == 'def':
                def_idx = idx
                break
        # merge def parts if needed
        sdef = self.synset.get_def().text()
        part_count = sdef.count(";")
        if part_count > 1:
            raws[def_idx] = "; ".join(raws[def_idx:def_idx + part_count])
            raws = raws[:def_idx + 1] + raws[def_idx + part_count:]
        # split def if needed
        return [r for r in raws if r]


class Gloss:
    def __init__(self, synset, origid, cat, gid):
        self.synset = synset
        self.gid = gid
        self.origid = origid  # Original ID from Gloss WordNet
        self.cat = cat
        self.items = []       # list of GlossItem objects
        self.tags = []        # Sense tags
        self.groups = []      # Other group labels
        self.__orig = None  # original surface form
        pass

    @property
    def surface(self):
        return self.__orig if self.__orig else self.text()

    @surface.setter
    def surface(self, value):
        self.__orig = value.strip()

    def get_tagged_sensekey(self):
        return [x.sk for x in self.tags if x]

    def get_gramwords(self, nopunc=True):
        tokens = []
        for item in self.items:
            words = [x for x in item.get_gramwords(nopunc) if x]
            tokens.extend(words)
        return tokens

    def add_gloss_item(self, tag, lemma, pos, cat, coll, rdf, origid, sep=None, text=None, itemid=-1):
        gt = GlossItem(self, tag, lemma, pos, cat, coll, rdf, origid, sep, text, itemid)
        gt.order = len(self.items)
        self.items.append(gt)
        return gt

    def tag_item(self, item, cat, tag, glob, glemma, glob_id, coll, origid, sid, sk, lemma, tagid=-1):
        tag = SenseTag(item, cat, tag, glob, glemma, glob_id, coll, origid, sid, sk, lemma, tagid)
        self.tags.append(tag)
        return tag

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx]

    def text(self):
        return StringTool.detokenize((x.text for x in self.items))

    def to_ttl(self, doc=None):
        """ Export to TextTagLib format (Read more: :mod:`~chirptext.texttaglib`) """
        sid = self.origid if self.origid else "{}{}_{}".format(self.synset.ID.offset, self.synset.ID.pos, self.cat)
        if doc is not None:
            sent = doc.new_sent(text=self.text())
        else:
            sent = ttl.Sentence(text=self.text())
        sent.new_tag(sid, tagtype='origid')
        colls = dd(list)
        item_map = {}
        # import tokens
        for item in self.items:
            tk = sent.new_token(text=item.text)
            item_map[item.origid] = tk
            # import token features
            if item.pos:
                tk.pos = item.pos
            if item.lemma:
                tk.lemma = item.lemma
            if item.tag:
                tk.new_tag(label=item.tag, tagtype="tag")
            tk.new_tag(label=item.origid, tagtype="origid")
            if item.coll:
                colls[item.coll].append(tk)  # mark this MWE
        # import concepts
        for tag in self.tags:
            if tag.coll:  # MWE
                c = sent.new_concept(tag=tag.sk, clemma=tag.lemma, tokens=colls[tag.coll])
            else:
                # single sense
                c = sent.new_concept(tag=tag.sk, clemma=tag.lemma, tokens=(item_map[tag.item.origid],))
            c.comment = tag.origid
        sent.fix_cfrom_cto()
        return sent

    def __repr__(self):
        return "gloss-%s" % (self.cat)

    def __str__(self):
        return "{Gloss('%s'|'%s') %s}" % (self.origid, self.cat, self.text())


class GlossItem:
    """ A word token (belong to a gloss)
    """
    def __init__(self, gloss, tag, lemma, pos, cat, coll, rdf, origid, sep=None, text=None, itemid=-1):
        self.itemid = itemid
        self.gloss = gloss
        self.order = -1
        self.tag = StringTool.strip(tag)
        self.lemma = StringTool.strip(lemma)
        self.pos = StringTool.strip(pos)
        self.cat = StringTool.strip(cat)
        self.coll = StringTool.strip(coll)
        self.rdf = StringTool.strip(rdf)
        self.sep = StringTool.strip(sep)
        self.text = StringTool.strip(text)
        self.origid = StringTool.strip(origid)
        pass

    def get_lemma(self):
        return self.text if self.text else self.lemma

    def get_gramwords(self, nopunc=True):
        """
        Return grammatical words from lemma
        E.g.
        prefer%2|preferred%3 => ['prefer', 'preferred']
        """
        if nopunc and self.cat == 'punc':
            return set()
        lemmata = set()
        if self.lemma is not None and len(self.lemma) > 0:
            tokens = self.lemma.split('|')
            for token in tokens:
                parts = token.split("%")
                lemmata.add(parts[0])
        return lemmata

    def __repr__(self):
        # return "l:`%s'" % (self.get_lemma())
        return "'%s'" % self.get_lemma()

    def __str__(self):
        return "(itemid: %s | id:%s | tag:%s | lemma:%s | pos:%s | cat:%s | coll:%s | rdf: %s | sep:%s | text:%s)" % (
            self.itemid, self.origid, self.tag, self.lemma, self.pos, self.cat, self.coll, self.rdf, self.sep, self.text)


class GlossGroup:
    """ A group tag (i.e. labelled GlossItem group)
    """

    def __init__(self, label=''):
        self.label = label
        self.items = []    # List of GlossItem belong to this group


class SenseTag:
    """ Sense annotation object
    """
    def __init__(self, item, cat, tag, glob, glemma, glob_id, coll, origid, sid, sk, lemma, tagid=-1):
        self.tagid = tagid         # tag id
        self.cat = cat             # coll, tag, etc.
        self.tag = tag             # from glob tag
        self.glob = glob           # from glob tag
        self.glemma = glemma       # from glob tag
        self.glob_id = glob_id     # from glob tag
        self.coll = coll           # from cf tag
        self.origid = origid       # from id tag
        self.sid = sid             # infer from sk & lemma
        self.gid = item.gloss.gid  # gloss ID
        self.sk = sk               # from id tag
        self.lemma = lemma          # from id tag
        self.item = item            # ref to gloss item (we can access gloss obj via self.item)

    def __repr__(self):
        return "%s (sk:%s)" % (self.lemma, self.sk)

    def __str__(self):
        return "%s (sk:%s | itemid: %s | cat:%s | tag:%s | glob:%s | glemma:%s | gid:%s | coll:%s | origid: %s)" % (
            self.lemma, self.sk, self.item.itemid, self.cat, self.tag, self.glob, self.glemma, self.glob_id, self.coll, self.origid)
