#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
YAWLib - Yet another WordNet library for Python

Latest version can be found at https://github.com/letuananh/yawlib

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

from .__version__ import __author__, __email__, __copyright__, __maintainer__
from .__version__ import __credits__, __license__, __description__, __url__
from .__version__ import __version_major__, __version_long__, __version__, __status__

from .config import YLConfig
from .models import SynsetID, POS, Synset, SynsetCollection
from .glosswordnet import GWordnetXML, GWordnetSQLite
from .wordnetsql import WordnetSQL
from .helpers import get_synset_by_id, get_synset_by_sk, get_synsets_by_term
from .helpers import dump_synsets, dump_synset
from .common import WordnetException, SynsetNotFoundException

__all__ = ['YLConfig', 'GWordnetXML', 'GWordnetSQLite', 'WordnetSQL',
           'POS', 'SynsetID', 'Synset', 'SynsetCollection',
           'get_synset_by_id', 'get_synset_by_sk',
           'get_synsets_by_term', 'dump_synsets', 'dump_synset',
           'WordnetException', 'SynsetNotFoundException',
           "__version__", "__author__", "__description__", "__copyright__"]
