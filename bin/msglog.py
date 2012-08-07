#!/usr/bin/env python
"""
Listens on the ibzmq broadcast endpoint and logs
messages into a sqlite database.

"""

from __future__ import print_function

import os
import logging

import zmq
import sqlite3

from ibzmq.proxy import DEFAULT_BROADCAST_ENDPOINT
from ibzmq.incoming import MESSAGE_NAMES, FIELD_DELIMITER

log = logging.getLogger(__name__)

DATABASE = 'message.db'

def create_schema(db):
    if not db.execute('SELECT * FROM sqlite_master WHERE name="messages"').fetchall():
        log.info('messages table not found: creating.')
        db.execute('CREATE TABLE messages (id INTEGER PRIMARY KEY, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, type INTEGER, content BLOB)')
        db.commit()

def insert_message(db, type, content):
    db.execute('INSERT INTO messages (type, content) VALUES (?,?)', (type, sqlite3.Binary(content)))
    db.commit()

def main():
    db = sqlite3.connect(DATABASE)
    create_schema(db)

    log.info('Inserting messages into {0}.'.format(os.path.abspath(DATABASE)))

    ctx = zmq.Context(1)
    s = ctx.socket(zmq.SUB)
    s.connect(DEFAULT_BROADCAST_ENDPOINT)
    s.setsockopt(zmq.SUBSCRIBE, '')

    log.info('Subcribed to {0}.'.format(DEFAULT_BROADCAST_ENDPOINT))

    while 1:
        msg = s.recv()
        fields = msg.split(FIELD_DELIMITER)
        msgid = int(fields[0])
        msgname = MESSAGE_NAMES.get(msgid, 'Unknown')
        log.info('Received. Field Count: {0:>2} Type: ({1:>02}) {2}'.format(len(fields), msgid, msgname))
        insert_message(db, msgid, msg)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
