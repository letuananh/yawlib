#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
YAWOL - Yet Another Wordnet Online (REST server)
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

import json
import logging

import flask
from flask import Flask, Response, abort
from functools import wraps
from flask import request
from chirptext.cli import CLIApp, setup_logging

from yawlib.config import read_config
from yawlib import YLConfig
from yawlib import SynsetID, SynsetCollection
from yawlib import WordnetSQL as WSQL


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


cfg = read_config()
logging_config_file = cfg.get('logging_config_file', 'logging.json')
log_dir = cfg.get('log_dir', 'logs')
setup_logging(logging_config_file, log_dir)
app = Flask(__name__, static_url_path="")
wsql = WSQL(YLConfig.WNSQL30_PATH)


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------
# Adopted from: http://flask.pocoo.org/snippets/79/
def jsonp(func):
    """Wraps JSONified output for JSONP requests."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        data = func(*args, **kwargs)
        callback = request.args.get('callback', False)
        if callback:
            content = "{}({})".format(str(callback), data)
            return Response(content, mimetype="application/javascript")
        else:
            return Response(data, mimetype="application/json")
    return decorated_function


# ---------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------
@app.route('/yawol/synset/<synsetid>', methods=['GET'])
@jsonp
def get_synset(synsetid):
    ss = wsql.get_synset_by_id(synsetid)
    if ss is not None:
        return ss.to_json_str()
    else:
        abort(404)


@app.route('/yawol/search/<query>', methods=['GET'])
@jsonp
def search(query):
    # assume that query is a synset?
    try:
        sid = SynsetID.from_string(query)
        ss = wsql.get_synset_by_id(sid)
        if ss is not None:
            return SynsetCollection().add(ss).to_json_str()
    except Exception as e:
        # not synsetid
        getLogger().exception(e, "Invalid synset ID")
        pass
    # try search by lemma
    synsets = wsql.get_synsets_by_lemma(query)
    if synsets:
        return synsets.to_json_str()
    else:
        # search by sensekey
        ss = wsql.get_synset_by_sk(query)
        if ss:
            return SynsetCollection().add(ss).to_json_str()
    # invalid query
    abort(404)


@app.route('/yawol/', methods=['GET'])
def index():
    return Response('Yawol {yv} - yawol-flask/Flask-{fv}'.format(yv=__version__, fv=flask.__version__), mimetype='text/html')


@app.route('/yawol/version', methods=['GET'])
@jsonp
def version():
    return json.dumps({'product': 'yawol',
                       'version': __version__,
                       'server': 'yawol-flask/Flask-{}'.format(flask.__version__)})


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def run_app(cli, args):
    print("Running Yawol-flask at http://{}:{} | DEBUG={}".format(args.host, args.port, args.debug))
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    cli = CLIApp(desc='Yawol-Flask development server', logger=__name__)
    cli.parser.add_argument('--port', default=5000, type=int)
    cli.parser.add_argument('--host', default='0.0.0.0')
    cli.parser.add_argument('--debug', default=False, action='store_true')
    cli.parser.set_defaults(func=run_app)
    cli.run()
