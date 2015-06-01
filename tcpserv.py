# tcpserv
#
# Copyright (c) 2015 Christian Sengstock, All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.

"""
Simple python socket helper library to implement
stateless tcp-servers.

Usage:

# Interface
>>> from tcpserv import listen, request
# Define server logic by a handler function:
# Gets a request string and returns a response string
>>> def my_handler(request): return "".join(reversed(request))
# Start the server
>>> listen("localhost", 55555, my_handler)
# Make requests
>>> for i in xrange(100):
>>>     print request("localhost", 55555, "request %d" % i)
"""

import thread
import socket
import struct

DATA_SIZE_TYPE = "!I"   # unsigned 4-byte int, network byte-order
# num of bytes; should always be 4;
# don't know if struct ensures this.
DATA_SIZE_LEN = len(struct.pack(DATA_SIZE_TYPE, 0))
if DATA_SIZE_LEN != 4:
    raise ValueError(
            "To work on different machines struct <!I> type should have " + \
            "4 bytes. This is an implementation error!")
MAX_DATA = 2**(DATA_SIZE_LEN*8)


def listen(host, port, handler):
    """
    Listens on "host:port" for requests
    and forwards traffic to the handler.
    The handler return value is then send
    to the client socket. A simple
    echo server handler:
    >>> def my_handler(request_string) return request_string

    The function blocks forever. Surround
    with an appropriate signal handler
    to quit the call (e.g., wait for
    a KeyboardInterrupt event):
    >>> try:
    >>>     listen("localhost", 55555, my_handler)
    >>> except KeyboardInterrupt, e:
    >>>     pass

    Args:
        host<str>: Listening host
        port<int>: Listening port
        handler<function>:
                   Function 'f(request_string)->response_string'
                   processing the request.
    """
    # Taken from
    # http://code.activestate.com/recipes/578247-basic-threaded-python-tcp-server/
    # Starts a new handler-thread for each request.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(1)
    while 1:
        clientsock, addr = sock.accept()
        thread.start_new_thread(_server, (clientsock, handler))


def request(host, port, data):
    """
    Sends data to server listening on "host:port" and returns
    the response.

    Args:
        host<str>: Server host
        port<int>: Server port
        data<str>: Request data
    Returns<str>:
        The response data
    """
    if type(data) != str:
        raise ValueError("data must be of type <str>")
    if len(data) > MAX_DATA:
        raise ValueError("request data must have len <= %d", MAX_DATA)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    b4 = struct.pack(DATA_SIZE_TYPE, len(data))
    sock.sendall(b4)
    sock.sendall(data)
    b4 = _recvn(sock, DATA_SIZE_LEN)
    n = struct.unpack(DATA_SIZE_TYPE, b4)[0]
    data = _recvn(sock, n)
    sock.close()
    return data


def _recvn(sock, n):
    """
    Reads exactly n bytes from the socket.
    """
    buf = []
    m = 0
    while m < n:
        pack = sock.recv(n-m)
        m += len(pack)
        buf.append(pack)
    return "".join(buf)


def _server(clientsock, handler):
    """
    Reads the request from the client socket
    and calls the handler callback to process the data.
    Sends back the response (return value of the
    handler callback) to the client socket.
    """
    b4 = _recvn(clientsock, DATA_SIZE_LEN)
    n = struct.unpack(DATA_SIZE_TYPE, b4)[0]
    req = _recvn(clientsock, n)
    resp = handler(req)
    if type(resp) != str:
        raise ValueError("handler return value must be of type <str>")
    if len(resp) > MAX_DATA:
        raise ValueError("handler return value must have len <= %d", MAX_DATA)
    b4 = struct.pack(DATA_SIZE_TYPE, len(resp))
    clientsock.sendall(b4)
    clientsock.sendall(resp)


def _test():
    import time
    def echo_handler(data):
        return data
    thread.start_new_thread(listen, ("localhost", 55555, echo_handler))
    # listen("localhost", 55555, echo_handler)
    time.sleep(1)
    print "generating data..."
    data = "1"*(2**28)
    print "starting communication..."
    for i in xrange(1000):
        print "request", i
        resp = request("localhost", 55555, data)
        print "received %.02f KB" % (len(resp)/1000.0)
        print "validation..."
        assert len(resp) == len(data)
        #for j,c in enumerate(data):
        #    assert(resp[j] == c)


if __name__ == "__main__":
    _test()