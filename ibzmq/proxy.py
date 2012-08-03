#!/usr/bin/env python
from __future__ import print_function

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint

from txzmq import ZmqFactory, ZmqEndpoint, ZmqREPConnection, ZmqEndpointType, ZmqPubConnection

from statemachine import StateMachine, State
from incoming import MESSAGE_SIZES

import logging
log = logging.getLogger(__name__)


# States for TWS protocol state machine.
Disconnected        = State('Disconnected')
Connecting          = State('Connecting')
WaitingForMessageID = State('WaitingForMessageID')
WaitingForMessage   = State('WaitingForMessage', 'fieldcount msgid msgversion')

Connecting.fieldcount          = 2
WaitingForMessageID.fieldcount = 2

class IBTWSProtocol(StateMachine, LineOnlyReceiver):
    delimiter = '\0'

    CLIENT_VERSION = 59

    states = { Disconnected,
               Connecting,
               WaitingForMessageID,
               WaitingForMessage }

    transitions = {
        Disconnected        : { Connecting },
        Connecting          : { WaitingForMessageID },
        WaitingForMessageID : { WaitingForMessage },
        WaitingForMessage   : { WaitingForMessageID },
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
            state_handler = getattr(self, 'fieldsReceived_' + self.state_name)
            state_handler(tuple(self._field_buffer))
            self._field_buffer = []

    #### State specific handling of field receipt ####

    def fieldsReceived_Connecting(self, fields):
        self.serverVersion = int(fields[0])
        self.connectionTime = fields[1]

        print(self.serverVersion, self.connectionTime)
        self._zmq_requests.setTWSProtocol(self)

        self.transition(WaitingForMessageID())

        self.writeField(self._clientid)

    def fieldsReceived_WaitingForMessageID(self, fields):
        msgid, msgversion = map(int, fields)
        log.debug('Message: {0} {1}'.format(msgid, msgversion))
        fieldcount = MESSAGE_SIZES.get(msgid, -1)
        self.transition(WaitingForMessage(fieldcount, msgid, msgversion))

    def fieldsReceived_WaitingForMessage(self, fields):
        log.debug('Contents: ' + repr(fields))
        self.publishFields((self.state.msgid, self.state.msgversion) + fields)
        self.transition(WaitingForMessageID())

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

class ZmqRequests(ZmqREPConnection):
    _twsprotocol = None

    def setTWSProtocol(self, protocol):
        self._twsprotocol = protocol

    def gotMessage(self, messageid, msg):
        print(repr(msg))
        if self._twsprotocol:
            self._twsprotocol.writeMessage(msg)
            self.reply(messageid, ZMQ_OK_RESPONSE)
        else:
            self.reply(messageid, ZMQ_ERR_RESPONSE)

class IBTWSProtocolFactory(Factory):
    def __init__(self, zmq_requests, zmq_broadcast):
        self.zmq_requests = zmq_requests
        self.zmq_broadcast = zmq_broadcast

    def buildProtocol(self, addr):
        return IBTWSProtocol(self.zmq_requests, self.zmq_broadcast)

def main():
    zmq_requests_factory = ZmqFactory()
    zmq_requests_endpoint = ZmqEndpoint(ZmqEndpointType.bind, "ipc:///var/tmp/ibproxy")
    zmq_requests = ZmqRequests(zmq_requests_factory, zmq_requests_endpoint)

    zmq_broadcast_factory = ZmqFactory()
    zmq_broadcast_endpoint = ZmqEndpoint(ZmqEndpointType.connect, "ipc:///var/tmp/ibproxyout")
    zmq_broadcast = ZmqPubConnection(zmq_broadcast_factory, zmq_broadcast_endpoint)

    api_endpoint = TCP4ClientEndpoint(reactor, "localhost", 4001)
    api_endpoint.connect(IBTWSProtocolFactory(zmq_requests, zmq_broadcast))
    reactor.run()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
