# tcpserv
Simple python socket helper library to implement stateless tcp-servers.

## Usage
Put the `tcpserv.py` file in your app-folder or anywhere in your `PYTHONPATH`.

### Set-up Server
```
# Define stateless server logic by a handler function
def my_handler(request): return "".join(reversed(request))

# Start the server (serves forever)
from tcpserv import listen
listen("localhost", 55555, my_handler)

# You can quit the call by catching signals, e.g., Ctrl-C:
try:
  listen("localhost", 55555, my_handler
except KeyboardInterrupt, e:
  pass
```

## Make Requests
```
from tcpserv import request
for i in xrange(100):
  print request("localhost", 55555, "request %d" % i)
```
