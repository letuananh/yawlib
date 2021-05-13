#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Global configuration file for YAWLib
"""

# This code is a part of yawlib library: https://github.com/letuananh/yawlib
# :copyright: (c) 2014 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
import logging

from texttaglib.chirptext import AppConfig
from texttaglib.chirptext.chio import read_file, write_file


MY_DIR = os.path.dirname(__file__)
CONFIG_TEMPLATE = os.path.join(MY_DIR, 'data', 'config_template.json')
__yawlib_home = os.environ.get('YAWLIB_HOME', MY_DIR)
__app_config = AppConfig('yawlib', mode=AppConfig.JSON, working_dir=__yawlib_home)


def full_path(a_path):
    return os.path.abspath(os.path.expanduser(a_path))


def getLogger():
    return logging.getLogger(__name__)


def _get_config_manager():
    """ Internal function for retrieving application config manager object
    Don't use this directly, use read_config() method instead
    """
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


def config_file_path():
    """ get config location """
    return _get_config_manager().locate_config()


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
