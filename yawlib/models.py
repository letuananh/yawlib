#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Shared data models
Latest version can be found at https://github.com/letuananh/yawlib

Adapted from: https://github.com/letuananh/lelesk

@author: Le Tuan Anh <tuananh.ke@gmail.com>
'''

# Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>
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
__copyright__ = "Copyright 2014, lelesk"
__credits__ = [ "Le Tuan Anh" ]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

########################################################################

import re

########################################################################

class POS:
    NOUN = 1
    VERB = 2
    ADJECTIVE = 3
    ADVERB = 4
    ADJECTIVE_SATELLITE = 5

    NUMS  = '12345'
    POSES = 'nvasr'
    num2pos_map = dict(zip(NUMS, POSES))
    pos2num_map = dict(zip(POSES, NUMS))

    def num2pos(pos_num):
        if pos_num not in POS.num2pos_map:
            raise Exception('Invalid POS number')
        return POS.num2pos_map[pos_num]

    def pos2num(pos):
        if pos not in POS.pos2num_map:
            raise Exception('Invalid POS')
        else:
            return POS.pos2num_map[pos]


class SynsetID:

    WNSQL_FORMAT = re.compile(r'(?P<pos>[12345])(?P<offset>\d{8})')
    CANONICAL_FORMAT = re.compile(r'(?P<offset>\d{8})-?(?P<pos>[nvasr])')

    def __init__(self, offset, pos):
        self.offset = offset
        self.pos = pos

    @staticmethod
    def from_string(synsetid):
        if synsetid is None:
            raise Exception("synsetid cannot be None")
        m = SynsetID.WNSQL_FORMAT.match(synsetid)
        if m:
            # WNSQL_FORMAT
            offset = m.group('offset')
            posnum = m.group('pos')
            return SynsetID(offset, POS.num2pos(posnum))
        else:
            # try canonical format
            m = SynsetID.CANONICAL_FORMAT.match(synsetid)
            if m:
                offset = m.group('offset')
                pos = m.group('pos')
                return SynsetID(offset, pos)
            else:
                raise Exception("Invalid synsetid format")

    def to_canonical(self):
        return "{offset}-{pos}".format(offset=self.offset, pos=self.pos)

    def to_wnsql(self):
        '''WordNet SQLite synsetID format
           Reference: https://sourceforge.net/projects/wnsql/'''
        return "{posnum}{offset}".format(offset=self.offset, posnum=POS.pos2num(self.pos))

    def __eq__(self, other):
        return other is not None and self.offset == other.offset and self.pos == other.pos

    def __repr__(self):
        return self.to_canonical()

    def __str__(self):
        return repr(self)


class SenseInfo:
    '''Store WordNet Sense Information (synsetID, pos, sensekey, etc.)
    '''

    def __init__(self, pos, synsetid, sensekey, wordid='', gloss='', tagcount=0, lemma=''):
        self.pos = pos
        self.sid = synsetid
        self.sk = sensekey
        self.wordid = wordid
        self.gloss = gloss
        self.tagcount = tagcount
        self.lemma = lemma

    @staticmethod
    def normalise_synsetid(sid):
        if len(sid) < 10:
            return '0' * (10 - len(sid)) + sid
        elif len(sid) > 10:
            return sid[-10:]
        else:
            return sid
    
    def get_full_sid(self):
        return self.pos + str(self.sid)[1:]
        
    def __repr__(self):
        return str(self)

    def get_canonical_synsetid(self):
        return '%s-%s' % (str(self.sid)[1:], self.pos)

    def get_gwn_sid(self):
        csid = self.get_canonical_synsetid()
        return csid[-1] + csid[:8]

    def __str__(self):
        return "SenseInfo: pos:%s | synsetid:%s | sensekey:%s | freq: %s" % (self.pos, self.get_canonical_synsetid(), self.sk, self.tagcount)

########################################################################

def main():
    jilog("This is a library, not a tool")

if __name__ == "__main__":
    main()
