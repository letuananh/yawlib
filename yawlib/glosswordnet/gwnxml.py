#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gloss WordNet XML Data Access Object - Access Gloss WordNet in XML format
"""

# This code is a part of yawlib library: https://github.com/letuananh/yawlib
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import logging
try:
    from lxml import etree
    _LXML_AVAILABLE = True
except Exception:
    _LXML_AVAILABLE = False
    from xml.etree import ElementTree as etree

from texttaglib.chirptext.leutile import StringTool, Counter

from yawlib.models import SynsetCollection

from .gwnmodels import GlossedSynset
from .gwnmodels import GlossRaw
# from .models import SenseKey
# from .models import Term
# from .models import Gloss
# from .models import GlossGroup
# from .models import SenseTag
# from .models import GlossItem

# -----------------------------------------------------------------------


class GWordnetXML:
    """ GWordNet XML Data Access Object
    """
    def __init__(self, filenames=None, memory_save=False, verbose=False):
        self.synsets = SynsetCollection()
        self.memory_save = memory_save
        self.verbose = verbose
        if filenames:
            self.filenames = filenames
            self.readfiles(filenames)

    def readfiles(self, files):
        """ Read from multiple XML files
        """
        for filename in files:
            self.read(filename)

    def read(self, filename):
        """ Read all synsets from an XML file
        """
        logging.info('Loading %s' % filename)
        with open(filename, 'rb') as infile:
            tree = etree.iterparse(infile)
            c = Counter()
            for event, element in tree:
                if event == 'end' and element.tag == 'synset':
                    synset = self.parse_synset(element)
                    element.clear()
                    self.synsets.add(synset)
                # end if end-synset
                c.count(element.tag)

            if self.verbose:
                c.summarise()
            return self.synsets

    def parse_synset(self, element):
        synset = GlossedSynset(element.get('id'))
        for child in element:
            if child.tag == 'terms':
                for grandchild in child:
                    # term is a lemma
                    if grandchild.tag == 'term':
                        synset.add_lemma(StringTool.strip(grandchild.text))
            elif child.tag == 'keys':
                for grandchild in child:
                    if grandchild.tag == 'sk':
                        synset.add_key(StringTool.strip(grandchild.text))
            elif child.tag == 'gloss' and child.get('desc') == 'orig' and not self.memory_save:
                if child[0].tag == 'orig':
                    synset.add_raw_gloss(GlossRaw.ORIG, StringTool.strip(child[0].text))
            elif child.tag == 'gloss' and child.get('desc') == 'text' and not self.memory_save:
                if child[0].tag == 'text':
                    synset.add_raw_gloss(GlossRaw.TEXT, StringTool.strip(child[0].text))
            elif child.tag == 'gloss' and child.get('desc') == 'wsd':
                for grandchild in child:
                    # [2016-02-12 LTA] aux should be parsed as well
                    # [2017-10-25 LTA] classif = domain
                    if grandchild.tag in ('def', 'ex', 'aux', 'classif'):
                        gloss = synset.add_gloss(origid=grandchild.get('id'), cat=StringTool.strip(grandchild.tag))
                        self.parse_gloss(grandchild, gloss)
                        # rip definition
                        pass
        return synset

    def parse_gloss(self, a_node, gloss):
        """ Parse a def node or ex node in Gloss WordNet
        """
        # What to be expected in a node? aux/mwf/wf/cf/qf
        # mwf <- wf | cf
        # aux <- mwf | qf | wf | cf
        # qf <- mwf | qf | wf | cf
        for child_node in a_node:
            self.parse_node(child_node, gloss)
        pass

    def parse_node(self, a_node, gloss):
        """ Parse node in a def node or an ex node.
            There are 5 possible tags:
            wf : single-word form
            cf : collocation form
            mwf: multi-word form
            qf : single- and double-quoted forms
            aux: auxiliary info
        """
        if a_node.tag == 'wf':
            return self.parse_wf(a_node, gloss)
        elif a_node.tag == 'cf':
            return self.parse_cf(a_node, gloss)
        elif a_node.tag == 'mwf':
            return self.parse_mwf(a_node, gloss)
        elif a_node.tag == 'qf':
            return self.parse_qf(a_node, gloss)
        elif a_node.tag == 'aux':
            return self.parse_aux(a_node, gloss)
        else:
            print("WARNING: I don't understand %s tag" % (a_node.tag))
        pass

    def tag_glossitem(self, id_node, glossitem, tag_obj):
        """ Parse ID element and tag a glossitem
        """
        sk = StringTool.strip(id_node.get('sk'))
        origid = StringTool.strip(id_node.get('id'))
        coll = StringTool.strip(id_node.get('coll'))
        lemma = StringTool.strip(id_node.get('lemma'))

        if tag_obj is None:
            tag_obj = glossitem.gloss.tag_item(glossitem, '', '', '', '', '', coll, origid, '', sk, lemma)
        else:
            tag_obj.itemid = glossitem.origid
            tag_obj.sk = sk
            tag_obj.origid = origid
            tag_obj.coll = coll
            tag_obj.lemma = lemma

        # WEIRD STUFF: lemma="purposefully ignored" sk="purposefully_ignored%0:00:00::"
        if lemma == 'purposefully ignored' and sk == "purposefully_ignored%0:00:00::":
            tag_obj.cat = 'PURPOSEFULLY_IGNORED'

    def get_node_text(self, wf_node):
        """ Return text value inside an XML node """
        if _LXML_AVAILABLE:
            return StringTool.strip(wf_node.xpath("string()"))
        else:
            # TODO: XML mixed content, don't use text attr here
            return wf_node.text
        

    def parse_wf(self, wf_node, gloss):
        """ Parse a word feature node and then add to gloss object
        """
        tag = wf_node.get('tag') if not self.memory_save else ''
        lemma = wf_node.get('lemma') if not self.memory_save else ''
        pos = wf_node.get('pos')
        cat = wf_node.get('type')  # if wf_node.get('type') else 'wf'
        coll = None  # wf_node.get('coll')
        rdf = wf_node.get('rdf')
        origid = wf_node.get('id')
        sep = wf_node.get('sep')
        text = self.get_node_text(wf_node)
        wf_obj = gloss.add_gloss_item(tag, lemma, pos, cat, coll, rdf, origid, sep, text, origid)
        # Then parse id tag if available
        for child in wf_node:
            if child.tag == 'id':
                self.tag_glossitem(child, wf_obj, None)
        return wf_obj

    def parse_cf(self, cf_node, gloss):
        """ Parse a word feature node and then add to gloss object
        """
        tag = cf_node.get('tag') if not self.memory_save else ''
        lemma = StringTool.strip(cf_node.get('lemma')) if not self.memory_save else ''
        pos = cf_node.get('pos')
        cat = cf_node.get('type')  # if cf_node.get('type') else 'cf'
        coll = cf_node.get('coll')
        rdf = cf_node.get('rdf')
        origid = cf_node.get('id')
        sep = cf_node.get('sep')
        text = self.get_node_text(cf_node)
        cf_obj = gloss.add_gloss_item(tag, lemma, pos, cat, coll, rdf, origid, sep, text, 'coll:' + coll)
        # Parse glob info if it's available
        for child_node in cf_node:
            if child_node.tag == 'glob':
                glob_tag = child_node.get('tag')
                glob_glob = child_node.get('glob')
                glob_lemma = child_node.get('lemma')
                glob_coll = child_node.get('coll')
                glob_id = child_node.get('id')
                #            def tag_item(self, item,   cat,  tag,      glob,      glemma,     gid,     coll,      origid, sid, sk, lemma):
                tag_obj = cf_obj.gloss.tag_item(cf_obj, 'cf', glob_tag, glob_glob, glob_lemma, glob_id, glob_coll, '', '', '', '')
                for grandchild in child_node:
                    if grandchild.tag == 'id':
                        self.tag_glossitem(grandchild, cf_obj, tag_obj)
        return cf_obj

    def parse_mwf(self, mwf_node, gloss):
        child_nodes = []
        for child_node in mwf_node:
            a_node = self.parse_node(child_node, gloss)
        # [TODO] Add mwf tag to child nodes

    def parse_qf(self, qf_node, gloss):
        child_nodes = [] 
        for child_node in qf_node:
            a_node = self.parse_node(child_node, gloss)
        # [TODO] Add qf tag to child nodes

    def parse_aux(self, aux_node, gloss):
        child_nodes = [] 
        for child_node in aux_node:
            a_node = self.parse_node(child_node, gloss)
        # [TODO] Add aux tag to child nodes
