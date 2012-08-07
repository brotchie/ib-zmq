#!/usr/bin/env python

##  _ _                                                                      ##
## (_) |__   ______ _ _ ___ _ __  __ _  IB-ZeroMQ - An Interactive Brokers   ##
## | | '_ \ |_ / -_) '_/ _ \ '  \/ _` |             TWS API to ZeroMQ Proxy  ##
## |_|_.__/ /__\___|_| \___/_|_|_\__, | (c) 2012, James Brotchie             ##
##                                  |_| http://zerotick.org/                 ##

"""
Listens on the ibzmq broadcast endpoint and logs
messages into a sqlite database.

"""

from __future__ import print_function

import os
import sys
import logging

import zmq
import sqlite3

from ibzmq.incoming import MESSAGE_NAMES, FIELD_DELIMITER
from ibzmq.config import Config

log = logging.getLogger(__name__)

def create_schema(db):
    if not db.execute('SELECT * FROM sqlite_master WHERE name="messages"').fetchall():
        log.info('messages table not found: creating.')
        db.execute('CREATE TABLE messages (id INTEGER PRIMARY KEY, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, type INTEGER, content BLOB)')
        db.commit()

def insert_message(db, type, content):
    db.execute('INSERT INTO messages (type, content) VALUES (?,?)', (type, sqlite3.Binary(content)))
    db.commit()

def main(database, config):
    db = sqlite3.connect(database)
    create_schema(db)

    log.info('Inserting messages into {0}.'.format(os.path.abspath(database)))

    ctx = zmq.Context(1)
    s = ctx.socket(zmq.SUB)
    s.connect(config['endpoint.broadcast'])
    s.setsockopt(zmq.SUBSCRIBE, '')

    log.info('Subcribed to {0}.'.format(config['endpoint.broadcast']))

    while 1:
        msg = s.recv()
        fields = msg.split(FIELD_DELIMITER)
        msgid = int(fields[0])
        msgname = MESSAGE_NAMES.get(msgid, 'Unknown')
        log.info('Received. Field Count: {0:>2} Type: ({1:>02}) {2}'.format(len(fields), msgid, msgname))
        insert_message(db, msgid, msg)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) != 3:
        print('Usage: {0} database config.yaml'.format(sys.argv[0]))
        sys.exit(1)

    database = sys.argv[1]
    config = Config(sys.argv[2])
    main(database, config)
