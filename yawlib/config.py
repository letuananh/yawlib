#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Global configuration file for YAWLib
Latest version can be found at https://github.com/letuananh/yawlib

Adapted from: https://github.com/letuananh/lelesk

@author: Le Tuan Anh <tuananh.ke@gmail.com>
'''

# Copyright (c) 2016, Le Tuan Anh <tuananh.ke@gmail.com>
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

import os
import logging

from chirptext import AppConfig
from chirptext.io import read_file, write_file


MY_DIR = os.path.dirname(__file__)
CONFIG_TEMPLATE = os.path.join(MY_DIR, 'data', 'config_template.json')
__yawlib_home = os.environ.get('YAWLIB_HOME', MY_DIR)
__app_config = AppConfig('yawlib', mode=AppConfig.JSON, working_dir=__yawlib_home)


def full_path(a_path):
    return os.path.abspath(os.path.expanduser(a_path))


def getLogger():
    return logging.getLogger(__name__)


def _get_config_manager():
    ''' Internal function for retrieving application config manager object
    Don't use this directly, use read_config() method instead
    '''
    return __app_config


def read_config():
    if not __app_config.config and not __app_config.locate_config():
        # need to create a config
        config_dir = os.path.expanduser('~/.yawlib/')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        cfg_loc = os.path.join(config_dir, 'config.json')
        default_config = read_file(CONFIG_TEMPLATE)
        getLogger().warning("Yawlib configuration file could not be found. A new configuration file will be generated at {}".format(cfg_loc))
        getLogger().debug("Default config: {}".format(default_config))
        write_file(cfg_loc, default_config)
    # read config
    config = __app_config.config
    return config


def home_dir():
    _config = read_config()
    yhome = _config.get('YAWLIB_HOME', '.')
    return yhome if yhome else __yawlib_home


def get_file(file_key):
    _config = read_config()
    return _config.get(file_key).format(YAWLIB_HOME=home_dir())


class YLConfig:
    # WordNet SQLite can be downloaded from:
    #       http://sourceforge.net/projects/wnsql/files/wnsql3/sqlite/3.0/
    WNSQL30_PATH = get_file('WNSQL30_PATH')
    # Gloss WordNet can be downloaded from:
    #       http://wordnet.princeton.edu/glosstag.shtml
    GWN30_PATH = get_file('GWN30_PATH')
    GWN30_DB = get_file('GWN30_DB')
    OMW_DB = get_file('OMW_DB')
    NTUMC_PRONOUNS = read_config().get('NTUMC_PRONOUNS')
