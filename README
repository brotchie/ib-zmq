# Interactive Brokers TWS API to ZeroMQ Proxy
This Python twisted application enables easier integration of the Interactive Brokers TWS API into zeromq based trading systems.

The TWS API is exposed to ZeroMQ clients through two sockets:
* A Router socket that forwards messages onto the TWS API. Because ZeroMQ messages are atomic TWS API requests are interleaved, allowing concurrent API access to multiple clients.
* A Publish socket that broadcasts all incoming messages. The proxy is aware of message types and lengths and will broadcast TWS API messages as individual ZeroMQ messages.
