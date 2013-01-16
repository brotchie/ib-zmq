#!/usr/bin/env python

##  _ _                                                                      ##
## (_) |__   ______ _ _ ___ _ __  __ _  IB-ZeroMQ - An Interactive Brokers   ##
## | | '_ \ |_ / -_) '_/ _ \ '  \/ _` |             TWS API to ZeroMQ Proxy  ##
## |_|_.__/ /__\___|_| \___/_|_|_\__, | (c) 2012, James Brotchie             ##
##                                  |_| http://zerotick.org/                 ##

from __future__ import print_function

import sys

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint

from txzmq import ZmqFactory, ZmqEndpoint, ZmqREPConnection, ZmqEndpointType, ZmqPubConnection

from statemachine import StateMachine, State
from incoming import MESSAGE_PARSERS, MESSAGE_NAMES, FieldCount, Done
from config import Config

from inspect import isgeneratorfunction

import logging
log = logging.getLogger(__name__)

# States for TWS protocol state machine.
Disconnected        = State('Disconnected')
Connecting          = State('Connecting')
WaitingForMessageID = State('WaitingForMessageID')
WaitingForGenerator = State('WaitingForGenerator', 'generator fieldcount cumfieldcount')

Connecting.fieldcount          = 2
WaitingForMessageID.fieldcount = 2

class IBTWSProtocol(StateMachine, LineOnlyReceiver):
    delimiter = '\0'

    CLIENT_VERSION = 59

    states = { Disconnected,
               Connecting,
               WaitingForMessageID,
               WaitingForGenerator }

    transitions = {
        Disconnected        : { Connecting },
        Connecting          : { WaitingForMessageID },
        WaitingForMessageID : { WaitingForGenerator },
        WaitingForGenerator : { WaitingForGenerator, WaitingForMessageID },
    }
    initial_state = Disconnected()
    
    def __init__(self, zmq_requests, zmq_broadcast, clientid=0):
        super(IBTWSProtocol, self).__init__()

        self._clientid = clientid
        self._field_buffer = []
        self._zmq_requests = zmq_requests
        self._zmq_broadcast = zmq_broadcast

        self.serverVersion = None
        self.connectionTime = None

    def connectionMade(self):
        self.writeField(self.CLIENT_VERSION)
        self.transition(Connecting())

    def lineReceived(self, field):
        self._field_buffer.append(field)

        if len(self._field_buffer) == self.state.fieldcount:
            self.fieldsReceived_dispatch(tuple(self._field_buffer))
            self._field_buffer = []

            if not self.state.fieldcount:
                self.fieldsReceived_dispatch(())

    def fieldsReceived_dispatch(self, fields):
        state_handler = getattr(self, 'fieldsReceived_' + self.state_name)
        state_handler(tuple(fields))

    #### State specific handling of field receipt ####

    def fieldsReceived_Connecting(self, fields):
        self.serverVersion = int(fields[0])
        self.connectionTime = fields[1]

        log.info("Connected. Server Version: {0} Connection Time: {1}".format(self.serverVersion, self.connectionTime))
        self._zmq_requests.setTWSProtocol(self)

        self.transition(WaitingForMessageID())

        self.writeField(self._clientid)

    def fieldsReceived_WaitingForMessageID(self, fields):
        msgid, msgversion = map(int, fields)
        msgname = MESSAGE_NAMES.get(msgid, 'Unknown')
        log.debug('Parsing: {0}({1}) {2}'.format(msgname, msgid, msgversion))
        parser = MESSAGE_PARSERS.get(msgid, None)

        if parser:
            generator = parser(msgid, msgversion)
            action, fieldcount = generator.next()
            assert action == FieldCount, 'Parsing generator must return a field count on first yield.'
            self.transition(WaitingForGenerator(generator, fieldcount, 2))
        else:
            log.error('Unimplemented message ID: {0}'.format(msgid))

    def fieldsReceived_WaitingForGenerator(self, fields):
        generator = self.state.generator
        cumfieldcount = self.state.cumfieldcount + len(fields)

        action, value = generator.send(fields)
        if action == FieldCount:
            self.transition(WaitingForGenerator(generator, value, cumfieldcount))
        elif action == Done:
            generator.close()

            msgid = int(value[0])
            msgname = MESSAGE_NAMES.get(msgid, 'Unknown')
            log.info('Message Parsed. Field Count: {0:>2}, Type: ({1:02}) {2}'.format(len(value), msgid, msgname))

            assert cumfieldcount == len(value), 'The number of consumed fields shall equal the length of the resulting message.'
            self.publishFields(value)
            self.transition(WaitingForMessageID())
        else:
            raise Expection('Unrecognised parser action {0}.'.format(action))

    #### Message writing and publishing methods ####

    def publishFields(self, fields):
        """
        Publishes a set of yields as an atomic message via
        ZeroMQ.

        """
        log.debug('Publishing ' + repr(fields))
        self._zmq_broadcast.send(self.delimiter.join(map(str, fields)) + self.delimiter)

    def writeField(self, field):
        self.transport.write(str(field) + self.delimiter)

    def writeFields(self, fields):
        assert fields, 'Cannot write zero count fields.'
        self.transport.write(self.delimiter.join(map(str, fields)) + self.delimiter)

    def writeMessage(self, msg):
        self.transport.write(msg)

ZMQ_OK_RESPONSE  = 'OK'
ZMQ_ERR_RESPONSE = 'ERR'

ZMQ_OOB_PREFIX = 'OOB'

class ZmqRequests(ZmqREPConnection):
    _twsprotocol = None

    def setTWSProtocol(self, protocol):
        self._twsprotocol = protocol

    def gotMessage(self, messageid, msg):
        # Handle OOB messages.
        if msg.startswith(ZMQ_OOB_PREFIX + '\0'):
            fields = msg.split('\0')
            if fields[1] == 'NOP':
                log.debug('Sending NOP response.')
                self.reply_ok(messageid)
            else:
                log.error('Unrecognized out-of-band message {0}.'.format(msg))
                self.reply_err(messageid)
        else:
            if self._twsprotocol:
                self._twsprotocol.writeMessage(msg)
                self.reply_ok(messageid)
            else:
                self.reply_err(messageid)

    def reply_ok(self, messageid):
        self.reply(messageid, ZMQ_OK_RESPONSE)

    def reply_err(self, messageid):
        self.reply(messageid, ZMQ_ERR_RESPONSE)

class IBTWSProtocolFactory(Factory):
    def __init__(self, zmq_requests, zmq_broadcast):
        self.zmq_requests = zmq_requests
        self.zmq_broadcast = zmq_broadcast

    def buildProtocol(self, addr):
        return IBTWSProtocol(self.zmq_requests, self.zmq_broadcast)

def main(config):
    zmq_requests_factory = ZmqFactory()
    zmq_requests_endpoint = ZmqEndpoint(ZmqEndpointType.bind, config['endpoint.command'])
    zmq_requests = ZmqRequests(zmq_requests_factory, zmq_requests_endpoint)

    zmq_broadcast_factory = ZmqFactory()
    zmq_broadcast_endpoint = ZmqEndpoint(ZmqEndpointType.bind, config['endpoint.broadcast'])
    zmq_broadcast = ZmqPubConnection(zmq_broadcast_factory, zmq_broadcast_endpoint)

    api_endpoint = TCP4ClientEndpoint(reactor, config['ibtws.host'], config['ibtws.port'])
    api_endpoint.connect(IBTWSProtocolFactory(zmq_requests, zmq_broadcast))
    reactor.run()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) != 2:
        print('Usage: {0} config.yaml'.format(sys.argv[0]))
        sys.exit(1)

    config = Config(sys.argv[1])
    main(config)
