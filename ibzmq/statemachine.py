##  _ _                                                                      ##
## (_) |__   ______ _ _ ___ _ __  __ _  IB-ZeroMQ - An Interactive Brokers   ##
## | | '_ \ |_ / -_) '_/ _ \ '  \/ _` |             TWS API to ZeroMQ Proxy  ##
## |_|_.__/ /__\___|_| \___/_|_|_\__, | (c) 2012, James Brotchie             ##
##                                  |_| http://zerotick.org/                 ##

from collections import namedtuple

def State(name, fields=''):
    return namedtuple(name, fields)

class StateMachine(object):
    """
    A simple state machine with enforced transitions and
    named tupled as states.

    """
    states = set()
    transitions = {}
    initial_state = None

    def __init__(self):
        assert self.states and \
               self.transitions and \
               self.initial_state is not None
        self._state = self.initial_state

    def transition(self, newstate):
        assert type(newstate) in self.transitions.get(type(self._state), ()), \
            'Transition from {0} to {1} invalid.'.format(self._state, newstate)
        self._state = newstate

    @property
    def state(self):
        return self._state

    @property
    def state_name(self):
        return type(self._state).__name__

    def is_state(self, statecheck):
        assert statecheck in self.states
        return statecheck == type(self._state)
