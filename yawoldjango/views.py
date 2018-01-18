#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
YAWOL-Django - Yet Another Wordnet Online (REST server) for Django
Latest version can be found at https://github.com/letuananh/yawlib

References:
    Python documentation:
        https://docs.python.org/
    PEP 257 - Python Docstring Conventions:
        https://www.python.org/dev/peps/pep-0257/

@author: Le Tuan Anh <tuananh.ke@gmail.com>
'''

# Copyright (c) 2017, Le Tuan Anh <tuananh.ke@gmail.com>
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
__copyright__ = "Copyright 2017, yawlib"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

########################################################################

import os
import json
import logging
import django
from django.http import HttpResponse, Http404
from yawlib import YLConfig
from yawlib import SynsetID, SynsetCollection
from yawlib import WordnetSQL as WSQL
from yawlib.omwsql import OMWSQL

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------
logger = logging.getLogger(__name__)
wsql = WSQL(YLConfig.WNSQL30_PATH)
omwsql = OMWSQL(YLConfig.OMW_DB) if os.path.isfile(YLConfig.OMW_DB) else None


def jsonp(func):
    ''' JSON/JSONP decorator '''
    def decorator(request, *args, **kwargs):
        objects = func(request, *args, **kwargs)
        # ignore HttpResponse
        if isinstance(objects, HttpResponse):
            return objects
        # JSON/JSONP response
        data = json.dumps(objects)
        if 'callback' in request.GET:
            callback = request.GET['callback']
        elif 'callback' in request.POST:
            callback = request.POST['callback']
        else:
            return HttpResponse(data, "application/json")
        # is JSONP
        # logging.debug("A jsonp response")
        data = '{c}({d});'.format(c=callback, d=data)
        return HttpResponse(data, "application/javascript")
    return decorator


@jsonp
def get_synset(request, synsetid):
    ''' Get a synset by ID
    Mapping: /yawol/synset/<synsetID> '''
    ss = wsql.get_synset_by_id(synsetid)
    if ss is None and omwsql is not None:
        # try to search in OMW
        ss = omwsql.get_synset(synsetid)
    if ss is not None:
        return ss.to_json()
    else:
        raise Http404("Synset doesn't exist")


@jsonp
def search(request, query):
    ''' Search by lemma, sensekey or synsetID
    Mapping: /yawol/search/<query>
    '''
    # assume that query is a synset?
    try:
        sid = SynsetID.from_string(query.strip())
        ss = wsql.get_synset(sid)
        if ss is None and omwsql is not None:
            # try to search by OMW
            print("Searching in OMW")
            ss = omwsql.get_synset(sid)
            print("OMW SS", ss)
        if ss is not None:
            return SynsetCollection().add(ss).to_json()
    except:
        logger.exception("Cannot find by synsetID")
        pass
    # try to search by lemma
    synsets = wsql.search(lemma=query)
    if synsets is not None and len(synsets) > 0:
        logger.info("Query: {} - Results: {}".format(query, synsets))
        return synsets.to_json()
    else:
        # try to search by sensekey
        try:
            ss = wsql.get_by_key(query)
        except:
            ss = None
        if ss:
            return SynsetCollection().add(ss).to_json()
    # invalid query
    raise Http404('Invalid query')


def index(request):
    ''' Yawol-django root '''
    return HttpResponse('Yawol {yv} - yawol-django/Django-{dv}'.format(yv=__version__, dv=django.get_version()), 'text/html')


@jsonp
def version(request):
    return {'product': 'yawol',
            'version': __version__,
            'server': 'yawol-django/Django-{}'.format(django.get_version())}
