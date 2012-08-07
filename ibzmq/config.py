##  _ _                                                                      ##
## (_) |__   ______ _ _ ___ _ __  __ _  IB-ZeroMQ - An Interactive Brokers   ##
## | | '_ \ |_ / -_) '_/ _ \ '  \/ _` |             TWS API to ZeroMQ Proxy  ##
## |_|_.__/ /__\___|_| \___/_|_|_\__, | (c) 2012, James Brotchie             ##
##                                  |_| http://zerotick.org/                 ##

import os
import yaml
import logging

log = logging.getLogger(__name__)

class Config(object):
    REQUIRED = {
        'ibtws.host', 'ibtws.port',
        'endpoint.command',
        'endpoint.broadcast',
    }

    def __init__(self, path):
        log.info('Loading proxy config from {0}.'.format(path))

        if not os.path.exists(path):
            raise IOError('Config at path {0} not found.'.format(path))

        config = yaml.load(file(path))

        if 'ibzmq' not in config:
            raise ValueError('ibzmq key not found in yaml config.')

        self._config = config['ibzmq']

        missing = Config.REQUIRED - set(self._config.keys())
        if missing:
            raise ValueError('Required config fields {0} not found.'.format(', '.join(missing)))

    def __getitem__(self, key):
        return self._config[key]
