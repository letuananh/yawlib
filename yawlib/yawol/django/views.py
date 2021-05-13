#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAWOL-Django - Yet Another Wordnet Online (REST server) for Django
"""

# This code is a part of yawlib library: https://github.com/letuananh/yawlib
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
import json
import logging
import django
from django.http import HttpResponse, Http404
from yawlib import SynsetID, SynsetCollection
from yawlib.helpers import get_omw, get_wn

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------
logger = logging.getLogger(__name__)
wsql = get_wn()
omwsql = get_omw()
print("OMW: {}".format(omwsql))


def jsonp(func):
    """ JSON/JSONP decorator """
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
    """ Get a synset by ID
    Mapping: /yawol/synset/<synsetID> """
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
    """ Search by lemma, sensekey or synsetID
    Mapping: /yawol/search/<query>
    """
    # assume that query is a synset?
    sid = SynsetID.from_string(query.strip(), default=None)
    if sid:
        ss = wsql.get_synset(sid)
        if ss is None and omwsql is not None:
            # try to search by OMW
            print("Searching in OMW")
            ss = omwsql.get_synset(sid)
            print("OMW SS", ss)
        if ss is not None:
            return SynsetCollection().add(ss).to_json()
    # try to search by lemma
    synsets = wsql.search(lemma=query)
    if synsets:
        logger.info("Query: {} - Results: {}".format(query, synsets))
        return synsets.to_json()
    else:
        if not synsets and omwsql is not None:
            print("Try to search {} in OMW".format(query))
            synsets = omwsql.search(lemma=query)
            if synsets:
                logger.info("Query: {} - Results: {}".format(query, synsets))
                return synsets.to_json()
            else:
                logger.warning("Not found {} in OMW".format(query))
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
    """ Yawol-django root """
    return HttpResponse('Yawol {yv} - yawol-django/Django-{dv}'.format(yv=__version__, dv=django.get_version()), 'text/html')


@jsonp
def version(request):
    return {'product': 'yawol',
            'version': __version__,
            'server': 'yawol-django/Django-{}'.format(django.get_version())}
