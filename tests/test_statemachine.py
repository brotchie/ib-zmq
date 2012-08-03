from py.test import raises

from ibzmq.statemachine import StateMachine, State

Connecting      = State('Connecting')
Connected       = State('Connected')
Waiting         = State('Waiting', 'message')
Disconnected    = State('Disconnected')

class ExampleStateMachine(StateMachine):
    states = { Connecting,
               Connected,
               Waiting,
               Disconnected }
    transitions = {
            Connecting : { Connected },
            Connected  : { Waiting },
            Waiting    : { Waiting, Disconnected },
    }

    initial_state = Connecting()


def test_successful_transitions():
    sm = ExampleStateMachine()
    assert sm.state == Connecting()

    sm.transition(Connected())
    assert sm.state == Connected()

    sm.transition(Waiting("message"))
    assert sm.state == Waiting("message")

    sm.transition(Waiting("message2"))
    assert sm.state == Waiting("message2")

    sm.transition(Disconnected())
    assert sm.state == Disconnected()

def test_invalid_transitions():
    sm = ExampleStateMachine()
    with raises(Exception):
        sm.transition(Disconnected())

def test_is_state():
    sm = ExampleStateMachine()
    assert sm.is_state(Connecting)

    sm.transition(Connected())
    assert sm.is_state(Connected)

def test_state_name():
    sm = ExampleStateMachine()
    assert sm.state_name == 'Connecting'

