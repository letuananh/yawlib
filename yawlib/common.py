#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared Wordnet features
"""

# This code is a part of yawlib library: https://github.com/letuananh/yawlib
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.


class WordnetException(Exception):
    """ Base class for Wordnet exception """
    pass


class WordnetFeatureNotSupported(WordnetException):
    pass


class SynsetNotFoundException(WordnetException):

    def __init__(self, synsetid):
        self.message = "Synset ID `{}' could not be found".format(synsetid)


class InvalidSynsetID(WordnetException):

    def __init__(self, synsetid):
        self.message = "`{}' is not a valid synset ID".format(synsetid)
