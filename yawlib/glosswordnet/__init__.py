# -*- coding: utf-8 -*-

"""
Gloss WordNet XML Data Access Object - Access Gloss WordNet in either XML or SQLite format

Usage:

from glosswordnet import XMLGWordNet
xmlwn = XMLGWordNet()
xmlwn.read(xml_file)
for ss in xmlwn.synsets:
    print(ss)

or
from glosswordnet import SQLiteGWordNet
"""

# This code is a part of yawlib library: https://github.com/letuananh/yawlib
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

from .gwnmodels import GlossedSynset, GlossRaw, Gloss, GlossItem, GlossGroup, SenseTag
from .gwnxml import GWordnetXML
from .gwnsqlite import GWordnetSQLite

__all__ = ['GlossedSynset', 'GWordnetXML', 'GWordnetSQLite',
           'GlossRaw', 'Gloss', 'GlossItem', 'GlossGroup', 'SenseTag']
