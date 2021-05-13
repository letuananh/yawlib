#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared data models
"""

# This code is a part of yawlib library: https://github.com/letuananh/yawlib
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import json
import re
import copy
from texttaglib.chirptext.leutile import uniquify
from .common import WordnetException, InvalidSynsetID

########################################################################


class POS(object):
    NOUN = 1
    VERB = 2
    ADJECTIVE = 3
    ADVERB = 4
    ADJECTIVE_SATELLITE = 5
    EXTRA = 6

    NUMS = '123456'
    POSES = 'nvarsx'
    num2pos_map = dict(zip(NUMS, POSES))
    pos2num_map = dict(zip(POSES, NUMS))

    @staticmethod
    def num2pos(pos_num):
        if not pos_num or str(pos_num) not in POS.num2pos_map:
            raise WordnetException('Invalid POS number')
        return POS.num2pos_map[str(pos_num)]

    @staticmethod
    def pos2num(pos):
        if pos not in POS.pos2num_map:
            raise WordnetException('Invalid POS')
        else:
            return POS.pos2num_map[pos]


class SynsetID(object):

    WNSQL_FORMAT = re.compile(r'(?P<pos>[123456nvarsx])(?P<offset>\d{8})')
    CANONICAL_FORMAT = re.compile(r'(?P<offset>\d{8})-?(?P<pos>[nvasrx])')

    def __init__(self, offset, pos):
        self.offset = offset
        self.pos = pos

    @staticmethod
    def from_string(synsetid, **kwargs):
        """ Parse a synsetID string to SynsetID object. When failed, return default argument is provided or an exception will be raised """
        if synsetid is None:
            if 'default' in kwargs:
                return kwargs['default']
            raise InvalidSynsetID("synsetid cannot be None")
        m = SynsetID.WNSQL_FORMAT.match(str(synsetid))
        if m:
            # WNSQL_FORMAT
            offset = m.group('offset')
            pos = m.group('pos')
            if pos in POS.NUMS:
                pos = POS.num2pos(pos)
            return SynsetID(offset, pos)
        else:
            # try canonical format
            m = SynsetID.CANONICAL_FORMAT.match(str(synsetid))
            if m:
                offset = m.group('offset')
                pos = m.group('pos')
                return SynsetID(offset, pos)
            else:
                if 'default' in kwargs:
                    return kwargs['default']
                raise InvalidSynsetID("Invalid synsetid format (provided: {})".format(synsetid))

    def to_canonical(self):
        """ Wordnet synset ID (canonical format: 12345678-x)
        """
        return "{offset}-{pos}".format(offset=self.offset, pos=self.pos)

    def to_wnsql(self):
        """WordNet SQLite synsetID format (112345678)
           Reference: https://sourceforge.net/projects/wnsql/"""
        return "{posnum}{offset}".format(offset=self.offset, posnum=POS.pos2num(self.pos))

    def to_gwnsql(self):
        """Gloss WordNet SQLite synsetID format (x12345678)"""
        return "{pos}{offset}".format(offset=self.offset, pos=self.pos)

    def __hash__(self):
        return hash(self.to_canonical())

    def __eq__(self, other):
        # make sure that the other instance is a SynsetID object
        if other and isinstance(other, Synset):
            other = other.ID
        if other and not isinstance(other, SynsetID):
            other = SynsetID.from_string(str(other))
        return other is not None and self.offset == other.offset and self.pos == other.pos

    def __lt__(self, other):
        # make sure that the other instance is a SynsetID object
        if other and not isinstance(other, SynsetID):
            other = SynsetID.from_string(str(other))
        return other is not None and self.offset < other.offset and self.pos < other.pos

    def __repr__(self):
        return self.to_canonical()

    def __str__(self):
        return repr(self)


class Synset(object):

    def __init__(self, sid, keys=None, lemmas=None, defs=None, exes=None, tagcount=0, lemma=None, lang='eng'):
        self.synsetid = sid  # synsetid.setter
        self.__keys = keys if keys is not None else []
        self.lemmas = lemmas if lemmas is not None else []
        self.__defs = defs if defs else []
        self.__exes = exes if exes else []
        self.tagcount = tagcount
        if lemma is not None:
            self.lemma = lemma  # Canonical lemma
        self.lang = lang
        pass

    @property
    def ID(self):
        return self.__sid

    @ID.setter
    def ID(self, value):
        if isinstance(value, SynsetID):
            self.__sid = copy.copy(value)
        else:
            self.__sid = SynsetID.from_string(value)

    @property
    def definition(self):
        return "; ".join(self.__defs)

    @definition.setter
    def definition(self, value):
        self.definitions = [x.strip() for x in value.split(";")]

    @property
    def definitions(self):
        return self.__defs

    @definitions.setter
    def definitions(self, values):
        self.__defs = values

    def add_def(self, definition):
        self.__defs.append(definition)

    @property
    def lemma(self):
        """ Synset canonical lemma """
        if self.lemmas is None or len(self.lemmas) == 0:
            return None
        else:
            return self.lemmas[0]

    @lemma.setter
    def lemma(self, value):
        if value is None:
            raise WordnetException("Canonical lemma cannot be None")
        if self.lemmas is None:
            self.lemmas = [value]
        elif len(self.lemmas) == 0:
            self.lemmas.append(value)
        else:
            self.lemmas[0] = value

    def add_lemma(self, value):
        if self.lemmas is None:
            self.lemmas = []
        self.lemmas.append(value)

    @property
    def sensekeys(self):
        return self.__keys

    def add_key(self, key):
        self.__keys.append(key)

    @property
    def examples(self):
        return self.__exes

    def add_example(self, example):
        self.__exes.append(example)

    # Aliases
    @property
    def synsetid(self):
        """ An alias of synset.ID """
        return self.__sid

    @synsetid.setter
    def synsetid(self, value):
        """ An alias of synset.ID """
        self.ID = value

    @property
    def keys(self):
        return self.sensekeys

    @property
    def defs(self):
        """ An alias of synset.definitions """
        return self.definitions

    @property
    def exes(self):
        """ An alias of synset.examples """
        return self.examples

    def get_tokens(self):
        tokens = []
        tokens.extend(self.lemmas)
        for l in self.lemmas:
            if ' ' in l:
                tokens.extend(l.split())
        return uniquify(tokens)

    def to_json(self):
        return {'synsetid': self.synsetid.to_canonical(),
                'definition': self.definition,
                'lemmas': self.lemmas,
                'sensekeys': self.sensekeys,
                'tagcount': self.tagcount,
                'examples': self.examples}

    def to_json_str(self):
        return json.dumps(self.to_json())

    def __eq__(self, other):
        return other is not None and isinstance(other, Synset) and self.ID == other.ID

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.ID)

    def __str__(self):
        return "Synset('{}')".format(self.synsetid)


class SynsetCollection(object):
    """ Synset collection which provides basic synset search function (by_sid, by_sk, etc.)
    """
    def __init__(self, synsets=None, lang='eng'):
        self.synsets = []
        self.sid_map = {}
        self.sk_map = {}
        if synsets:
            for synset in synsets:
                self.add(synset)
        self.lang = lang

    def add(self, synset):
        self.synsets.append(synset)
        self.sid_map[synset.ID] = synset
        for key in synset.sensekeys:
            self.sk_map[key] = synset
        return self

    def __getitem__(self, sid):
        if not isinstance(sid, SynsetID):
            sid = SynsetID.from_string(sid)
        return self.sid_map[sid]

    def __contains__(self, sid):
        if not isinstance(sid, SynsetID):
            sid = SynsetID.from_string(sid)
        return sid in self.sid_map

    def __len__(self):
        return self.count()

    def by_sid(self, sid):
        if sid and sid in self.sid_map:
            return self.sid_map[str(sid)]
        else:
            return None

    def by_sk(self, sk):
        if sk in self.sk_map:
            return self.sk_map[sk]
        else:
            return None

    def __iter__(self):
        return iter(self.synsets)

    def count(self):
        return len(self.synsets)

    def merge(self, another_scol):
        """ Add synsets from another synset collection """
        for synset in another_scol.synsets:
            if synset.ID not in self:
                self.add(synset)
        return self

    def __str__(self):
        return str(self.synsets)

    def to_json(self):
        return [x.to_json() for x in self]

    def to_json_str(self):
        return json.dumps(self.to_json())
