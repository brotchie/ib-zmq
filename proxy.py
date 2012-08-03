#!/usr/bin/env python

from __future__ import print_function

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint

from txzmq import ZmqFactory, ZmqEndpoint, ZmqREPConnection, ZmqEndpointType, ZmqPubConnection

# Incoming message ids.
TICK_PRICE		= 1
TICK_SIZE		= 2
ORDER_STATUS	= 3
ERR_MSG		= 4
OPEN_ORDER         = 5
ACCT_VALUE         = 6
PORTFOLIO_VALUE    = 7
ACCT_UPDATE_TIME   = 8
NEXT_VALID_ID      = 9
CONTRACT_DATA      = 10
EXECUTION_DATA     = 11
MARKET_DEPTH     	= 12
MARKET_DEPTH_L2    = 13
NEWS_BULLETINS    	= 14
MANAGED_ACCTS    	= 15
RECEIVE_FA    	    = 16
HISTORICAL_DATA    = 17
BOND_CONTRACT_DATA = 18
SCANNER_PARAMETERS = 19
SCANNER_DATA       = 20
TICK_OPTION_COMPUTATION = 21
TICK_GENERIC = 45
TICK_STRING = 46
TICK_EFP = 47
CURRENT_TIME = 49
REAL_TIME_BARS = 50
FUNDAMENTAL_DATA = 51
CONTRACT_DATA_END = 52
OPEN_ORDER_END = 53
ACCT_DOWNLOAD_END = 54
EXECUTION_DATA_END = 55
DELTA_NEUTRAL_VALIDATION = 56
TICK_SNAPSHOT_END = 57
MARKET_DATA_TYPE = 58
COMMISSION_REPORT = 59

MESSAGE_SIZES = {
    TICK_PRICE:               5,
    TICK_SIZE:                3,
    ORDER_STATUS:             10,
    ERR_MSG:                  None,
    OPEN_ORDER:               None,
    ACCT_VALUE:               4,
    PORTFOLIO_VALUE:          17,
    ACCT_UPDATE_TIME:         1,
    NEXT_VALID_ID:            1,
    CONTRACT_DATA:            None,
    EXECUTION_DATA:           None,
    MARKET_DEPTH:             None,
    MARKET_DEPTH_L2:          None,
    NEWS_BULLETINS:           None,
    MANAGED_ACCTS:            1,
    RECEIVE_FA:               None,
    HISTORICAL_DATA:          None,
    BOND_CONTRACT_DATA:       None,
    SCANNER_PARAMETERS:       None,
    SCANNER_DATA:             None,
    TICK_OPTION_COMPUTATION:  10,
    TICK_GENERIC:             3,
    TICK_STRING:              3,
    TICK_EFP:                 9,
    CURRENT_TIME:             None,
    REAL_TIME_BARS:           None,
    FUNDAMENTAL_DATA:         None,
    CONTRACT_DATA_END:        None,
    OPEN_ORDER_END:           None,
    ACCT_DOWNLOAD_END:        1,
    EXECUTION_DATA_END:       None,
    DELTA_NEUTRAL_VALIDATION: None,
    TICK_SNAPSHOT_END:        None,
    MARKET_DATA_TYPE:         None,
    COMMISSION_REPORT:        None,
}

# Outgoing messgae ids.
REQ_MKT_DATA                = 1
CANCEL_MKT_DATA             = 2
PLACE_ORDER                 = 3
CANCEL_ORDER                = 4
REQ_OPEN_ORDERS             = 5
REQ_ACCOUNT_DATA            = 6
REQ_EXECUTIONS              = 7
REQ_IDS                     = 8
REQ_CONTRACT_DATA           = 9
REQ_MKT_DEPTH               = 10
CANCEL_MKT_DEPTH            = 11
REQ_NEWS_BULLETINS          = 12
CANCEL_NEWS_BULLETINS       = 13
SET_SERVER_LOGLEVEL         = 14
REQ_AUTO_OPEN_ORDERS        = 15
REQ_ALL_OPEN_ORDERS         = 16
REQ_MANAGED_ACCTS           = 17
REQ_FA                      = 18
REPLACE_FA                  = 19
REQ_HISTORICAL_DATA         = 20
EXERCISE_OPTIONS            = 21
REQ_SCANNER_SUBSCRIPTION    = 22
CANCEL_SCANNER_SUBSCRIPTION = 23
REQ_SCANNER_PARAMETERS      = 24
CANCEL_HISTORICAL_DATA      = 25
REQ_CURRENT_TIME            = 49
REQ_REAL_TIME_BARS          = 50
CANCEL_REAL_TIME_BARS       = 51
REQ_FUNDAMENTAL_DATA        = 52
CANCEL_FUNDAMENTAL_DATA     = 53
REQ_CALC_IMPLIED_VOLAT      = 54
REQ_CALC_OPTION_PRICE       = 55
CANCEL_CALC_IMPLIED_VOLAT   = 56
CANCEL_CALC_OPTION_PRICE    = 57
REQ_GLOBAL_CANCEL           = 58
REQ_MARKET_DATA_TYPE        = 59

class NullDelimitedReceiver(LineOnlyReceiver):
    delimiter = '\x00'

class IBTWSProtocol(NullDelimitedReceiver):
    CLIENT_VERSION = 59
    
    STATE_CONNECTING = 0
    STATE_WAITING_MSGID  = 1
    STATE_WAITING_MESSAGE  = 2

    def __init__(self, zmq_incoming, zmq_outgoing, clientid=0):
        self._clientid = clientid
        self._state = IBTWSProtocol.STATE_CONNECTING
        self._field_buffer = []
        self._expected_field_count = -1
        self._zmq_incoming = zmq_incoming
        self._zmq_outgoing = zmq_outgoing
        self._last_msgid = None
        self._last_msgversion = None

        self.serverVersion = None
        self.connectionTime = None

    def connectionMade(self):
        self.writeField(self.CLIENT_VERSION)
        self.expectFields(2)

    def lineReceived(self, field):
        assert self._expected_field_count > 0
        assert len(self._field_buffer) != self._expected_field_count

        self._field_buffer.append(field)
        if len(self._field_buffer) == self._expected_field_count:
            self._expected_field_count = -1
            self.fieldsReceived(self._field_buffer)
            self._field_buffer = []

    def fieldsReceived(self, fields):
        if self._state == IBTWSProtocol.STATE_CONNECTING:
            self.serverVersion = int(fields[0])
            self.connectionTime = fields[1]

            print(self.serverVersion, self.connectionTime)
            self._zmq_incoming.setTWSProtocol(self)

            self._state = IBTWSProtocol.STATE_WAITING_MSGID

            self.writeField(self._clientid)

            # Expect message type and message version as next fields.
            self.expectFields(2)
        elif self._state == IBTWSProtocol.STATE_WAITING_MSGID:
            self._last_msgid = int(fields[0])
            self._last_msgversion = int(fields[1])

            print(self._last_msgid, self._last_msgversion)

            self._state = IBTWSProtocol.STATE_WAITING_MESSAGE
            self.expectFields(MESSAGE_SIZES.get(self._last_msgid, -1))
        else:
            print(fields)
            self.publishFields([self._last_msgid, self._last_msgversion] + fields)
            self._state = IBTWSProtocol.STATE_WAITING_MSGID

            self.expectFields(2)
            self._last_msgid = None
            self._last_msgversion = None

    def publishFields(self, fields):
        print("Publishing " + repr(fields))
        self._zmq_outgoing.send(self.delimiter.join(map(str, fields)) + self.delimiter)

    def expectFields(self, count):
        self._expected_field_count = count

    def writeField(self, field):
        self.transport.write(str(field) + self.delimiter)

    def writeFields(self, fields):
        assert fields
        self.transport.write(self.delimiter.join(map(str, fields)) + self.delimiter)

    def writeMessage(self, msg):
        self.transport.write(msg)

class ZmqIncoming(ZmqREPConnection):
    _twsprotocol = None

    def setTWSProtocol(self, protocol):
        self._twsprotocol = protocol

    def gotMessage(self, messageid, msg):
        print(repr(msg))
        if self._twsprotocol:
            self._twsprotocol.writeMessage(msg)
        self.reply(messageid, "OK")

class IBTWSProtocolFactory(Factory):
    def __init__(self, zmq_incoming, zmq_outgoing):
        self.zmq_incoming = zmq_incoming
        self.zmq_outgoing = zmq_outgoing

    def buildProtocol(self, addr):
        return IBTWSProtocol(self.zmq_incoming, self.zmq_outgoing)

def main():
    zmq_incoming_factory = ZmqFactory()
    zmq_incoming_endpoint = ZmqEndpoint(ZmqEndpointType.bind, "ipc:///var/tmp/ibproxy")
    zmq_incoming = ZmqIncoming(zmq_incoming_factory, zmq_incoming_endpoint)

    zmq_outgoing_factory = ZmqFactory()
    zmq_outgoing_endpoint = ZmqEndpoint(ZmqEndpointType.connect, "ipc:///var/tmp/ibproxyout")
    zmq_outgoing = ZmqPubConnection(zmq_outgoing_factory, zmq_outgoing_endpoint)

    point = TCP4ClientEndpoint(reactor, "localhost", 4001)
    point.connect(IBTWSProtocolFactory(zmq_incoming, zmq_outgoing))
    reactor.run()

if __name__ == '__main__':
    main()
