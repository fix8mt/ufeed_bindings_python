# UFEed Python Binding

-   [Introduction](#introduction)
-   [Getting Started](#getting-started)
-   [Demo](#demo)
    -   [Requests](#requests)
    -   [Subscribing](#subscribing)
    -   [Responding](#responding)
    -   [Publishing](#publishing)
    -   [Finishing Up](#finishing-up)
-   [Message](#message)
-   [Interface](#interface)
    -   [UFEedClient](#ufeedclient)
    -   [Message and Message Builder](#message-and-message-builder)
-   [Constants](#constants)
    -   [FIX variants constants](#fix-variants-constants)
-   [Logging](#logging)

------------------------------------------------------------------------

# Introduction

The UFEed Python Adapter (`UFEed_Python`) provides a low level Pythonic interface
to the UFEGW. Interactions with the UFEGW are based around a
`UFEedClient` object which can be used to send and receive *Messages* to
and from the UFEGW.

Use the following [Universal FIX engine documentaion](https://fix8mt.atlassian.net/wiki/spaces/FMT/pages/634438/Universal|FIX|Engine|Home) for a reference.

Features of `UFEedClient`:

-   System API support (see [4. Implementation Guide - Section
    1.3](https://fix8mt.atlassian.net/wiki/spaces/FMT/pages/628308/4.|Implementation|Guide))
-   Business API support (eg. NewOrderSingle and standard FIX messages)
-   Provides a 4-way communications API in order to make requests,
    publish messages, receive responses and subscribe to broadcast
    messages
-   User defined functions to handle these PUB, SUB, REQ and REP message
    events
-   Dynamic configuration of PUB, SUB, REQ, REP addressing and topics
-   Internal session management

Features of a `Message`:

-   A `Message` object is automatically mapped onto its internal fields,
    with inspection via **message\[tag\] = value**
-   An inheritance interface for implementers to enforce required
    fields, as well as provide polymorphic/functional enhancements for
    specialised `Message` types
-   Smart field creation, rendering field value to *ival*, *sval* or
    *fval* depending on context
-   Named `Message` properties (*name, longname, seq, service_id,
    subservice_id*)
-   Pretty printing of messages

# Getting Started

The `UFEed_Python` builds to a compiled Python module in both *.so* (Linux and
MacOS) and *.pyd* (Windows) format. It has dependencies on the Python
*pyzmq* and *protobuf* libraries. Within the distributed `UFEed_Python` archive we find the following directory structure (example is Linux / MacOS):

```
py
├── README.md
├── requirements.txt
├── test_message.py
├── test_ufeedclient.py
└── ufeed_bindings_python
    ├── __init__.py
    ├── consts.cpython-<python_version>-<platform>-<OS>.so
    ├── message.cpython-<python_version>-<platform>-<OS>.so
    ├── ufeapi_pb2.cpython-<python_version>-<platform>-<OS>.so
    ├── ufeedclient.cpython-<python_version>-<platform>-<OS>.so
    ├── ufe_py_fields_fix40.cpython-<python_version>-<platform>-<OS>.so
    ├── ufe_py_fields_fix41.cpython-<python_version>-<platform>-<OS>.so
    ├── ufe_py_fields_fix42.cpython-<python_version>-<platform>-<OS>.so
    ├── ufe_py_fields_fix43.cpython-<python_version>-<platform>-<OS>.so
    ├── ufe_py_fields_fix44.cpython-<python_version>-<platform>-<OS>.so
    ├── ufe_py_fields_fix50.cpython-<python_version>-<platform>-<OS>.so
    ├── ufe_py_fields_fix50sp1.cpython-<python_version>-<platform>-<OS>.so
    └── ufe_py_fields_fix50sp2.cpython-<python_version>-<platform>-<OS>.so
```

The easiest way to run the `UFEed_Python` is within a Python virtual environment. If virtualenv is not installed on the machine, it can be installed via:

**Linux**
```shell
$ sudo apt install virtualenv
```
**Windows / MacOS**
```shell
> pip install virtualenv
```

After this is done, inside the `UFEed_Python` directory we enter the following
commands:

**Linux / MacOS**
```shell
$ virtualenv -p python3 venv
$ source venv/bin/activate
$ pip install -r requirements.txt # installs pyzmq and protobuf
```
**Windows**
```shell
> virtualenv venv
> ./venv/Scripts/activate
> pip install -r requirements.txt # installs pyzmq and protobuf
```

The environment is now ready to execute the `UFEed_Python`.

# Demo

**Note that this tutorial is relatively detailed, and demonstrates some
more advanced concepts in `UFEed_Python` usage. From within the `UFEed_Python` directory, either in a Python script, or via a
Python interpreter, we can import the `UFEed_Python` and all its necessary
machinery using:

```python
from UPA import *
```

Then we create a `UFEedClient` object:

```python
uc = UFEedClient()
```


We now need to create user defined functions to handle the REQ and SUB
messages that the `UFEedClient` can make to and receive from the UFEGW.
In this simple case, we decide that when certain messages are received
we will print them, like so:

```python
def subscriber_func(msg):
    if msg.service_id == UFE_CMD_LOGIN or msg.longname == "ExecutionReport":
        print(msg)

def requester_func(msg):
    print(msg)
```

These methods are the minimal amount of functional behaviour that must
be defined in order to use the `UFEed_Python`. For the subscriber function, we have applied a filter to only print login commands or execution reports
because typically the UFEGW will have a plethora of messages coming
through at any given time. You can try this out in the future by
defining `subscriber_func` as a simple `print(msg)`. For now though we
proceed by starting the `UFEedClient` with the function definitions
above:

```python
uc.start(sub_func=subscriber_func, req_func=requester_func)
```

## Requests

The `UFEed_Python` manages its requests via the `REQUESTER` connection string, and its topic via the `REQUESTER_TOPIC`. In this run-through example we are using the defaults ("tcp://127.0.0.1:55746" and
"ufeedclient-responder") by not specifying them explicitly.

If we want to specify these values we define them in a dictionary:

```python
conn_strs = {REQUESTER: 'tcp://127.0.0.1:55746',
             REQUESTER_TOPIC: 'ufeedclient-responder'}
```

and pass them to the UFEedClient at instantiation:

```python
uc = UFEedClient(conn_strs)
```

With the `UFEedClient` started, it is now ready to interact with the
UFEGW. We should start by logging in:

```python
login = uc.create_message() \
    .set_long_name("login") \
    .set_type(st_system) \
    .set_service_id(UFE_CMD_LOGIN) \
    .add_field(UFE_CMD, UFE_CMD_LOGIN) \
    .add_field(UFE_LOGIN_ID, "user01") \
    .add_field(UFE_LOGIN_PW, "password123456")
# login is Message.Builder
response = uc.request(login)
```

If our user credentials are valid, we should receive back a `Message`
from the UFEGW confirming our login. Because we are printing login
`Message` responses automatically, a message similar to the following
should be printed in the Python console:

```
seq: 5
type: st_response
service_id: 73001
fields {
  location: fl_system
  type: ft_status
  tag: 72001
  ival: 71013
}
fields {
  location: fl_system
  type: ft_int
  tag: 80045
  ival: 5
}
fields {
  location: fl_system
  type: ft_int
  tag: 72010
  ival: 73001
}
fields {
  location: fl_system
  type: ft_uuid
  tag: 72005
  sval: "\246[V\275^\006N\254\202\336\212\312\266\3544\217"
}
fields {
  location: fl_system
  type: ft_string
  tag: 80058
  sval: "logon success"
}
```

This means we have now logged on successfully, and we can now perform
both System and Business API calls. Incidentally, we also now have a
response from UFEGW that we can query. This message is stored in the
`response` variable, and we could query (for example), the session token
provided by the UFEGW server using:

```python
response[UFE_SESSION_TOKEN]
```

In this example we see the
value **\"\\246\[V\\275\^\\006N\\254\\202\\336\\212\\312\\266\\3544\\217\"**,
which is an *sval* binary format.

Note that this is just an example of probing a message for a specific
value - the `UFEedClient` will manage the session using this token on
our behalf, so we don\'t need to do anything specifically with it. For
any additional messaging to the UFEGW, we don\'t need to worry about
explicitly providing this token in any of our requests.

With our login out of the way, we can proceed with some more meaningful
interactions. Let\'s try submitting an order:

```python
nos = uc.create_message()
    .set_long_name("NewOrderSingle")
    .set_type(MsgType.st_fixmsg)
    .set_service_id(6) # set service id manually
nos.name = "D"
# adds fields by list of tuple pairs
nos.add_fields([
    (COMMON_SYMBOL, "BHP"), 
    (COMMON_CLORDID, "Ord01"), 
    (COMMON_ORDERQTY, 100.), 
    (COMMON_PRICE, 10.25), 
    (COMMON_ORDTYPE, '1'), 
    (COMMON_SIDE, '0'), 
    (COMMON_TIMEINFORCE, '2'), 
    (COMMON_TRANSACTTIME, "now")])
response = uc.request(nos)
```

So long as our UFEGW environment is properly configured (see **4.
Implementation Guide, section 7** for help with this), and we create a
`Message` with a relevant service ID, our successful *NewOrderSingle*
should generate 1 to N Execution Reports. The UFEGW communications model
is such that when we make our request via a request() function, we then
receive these reports via a UFEGW broadcast in our subscriber function
(the UFEedClient started actively listening to these subscription
broadcasts on our behalf when we started it). When these messages
arrive, because of the way we defined our *subscriber_func* above, each
Execution Report will now print. They will look something like this:

```
name: "8"
longname: "ExecutionReport"
seq: 2889
service_id: 6
fields {
  location: fl_header
  type: ft_string
  tag: 35
  sval: "8"
}
fields {
  location: fl_header
  type: ft_int
  tag: 34
  ival: 602
}
fields {
  location: fl_header
  type: ft_time
  tag: 52
  ival: 1557878840437000000
}
fields {
  type: ft_string
  tag: 37
  sval: "ord2"
}
fields {
  type: ft_string
  tag: 11
  sval: "Ord01"
}
fields {
  type: ft_string
  tag: 17
  sval: "exec7"
}
fields {
  type: ft_char
  tag: 150
  sval: "0"
}
fields {
  type: ft_char
  tag: 39
  sval: "0"
}
fields {
  type: ft_string
  tag: 55
  sval: "ALLSYM:BHP"
}
... and so on
```

## Subscribing

The `UFEed_Python` manages its subscriptions via the SUBSCRIBER connection string, and its topic via the `SUBSCRIBER_TOPIC`. In this run-through example we are using the defaults (\"tcp://127.0.0.1:55745\" and
\"ufegw-publisher\") by not specifying them explicitly.

If we want to specify these values we define them in a dictionary:

```python
conn_strs = {SUBSCRIBER: 'tcp://127.0.0.1:55745',
             SUBSCRIBER_TOPIC: 'ufegw-publisher'}
```

and pass them to the UFEedClient at instantiation:

```python
uc = UFEedClient(conn_strs)
```

The UFEGW does not just provide responses to our `UFEed_Python` requests. It also publishes messages with UFEGW status updates that can be received by a
subscriber. The `UFEed_Python` actively subscribes to these messages after the
`UFEedClient.start()` function has been called.

We already got a sense of the `UFEed_Python` subscriber in the previous section, when a *NewOrderSingle* request sent by the `UFEed_Python` resulted in the UFEGW publishing our Execution Reports in response. In that instance we simply printed the reports, but it is worth delving a little deeper into this subscription functionality and its possibilities.

Subscribing to important messages from the UFEGW gives us an opportunity
to gather, process and store information that is relevant to us via our
client. When we defined our subscription function
that we passed to start(), we specified a simple filter - to print login
command responses or Execution Reports:

```python
def subscriber_func(msg):
    # msg is Message
    if msg.service_id == UFE_CMD_LOGIN or msg.longname == "ExecutionReport":
        print(msg)
```

However, we may wish to introduce additional functionality in the way we
handle messages, rather than just printing every single Execution Report
message we receive on our subscription channel without discrimination.

To start with, rather than just printing these reports, it may be more
useful for us to store them programmatically. We could catalogue the
Execution Reports in a simple list:

```python
execution_reports = []

def subscriber_func(msg):
    if msg.longname == "ExecutionReport":
        execution_reports.append(msg)

# ... program logic
# ... do something with execution_reports
```

Or perhaps filter execution reports by a specific symbol:

```python
BHP_exec_reports = []

def subscriber_func(msg):
    if msg.longname == "ExecutionReport" and msg[COMMON_SYMBOL] == "ALLSYM:BHP":
        BHP_exec_reports.append(msg)
```

## Responding

The `UFEed_Python` manages its responses via the `RESPONDER` connection string, and its topic via the `RESPONDER_TOPIC`. In this run-through example we are using the defaults (\"tcp://\*:55748\" and \"ufegw-responder\") by not
specifying them explicitly.

If we want to specify these values we define them in a dictionary:

```python
conn_strs = {RESPONDER: 'tcp://*:55748',
             RESPONDER_TOPIC: 'ufegw-responder'}
```

and pass them to the UFEedClient at instantiation:

```python
uc = UFEedClient(conn_strs)
```

As well as listening for published broadcasts, after its start()
function is invoked the `UFEed_Python` will also start actively listen for requests
sent to it via a requesting client elsewhere. Note that in order to do
anything with this requests, we must define a *responder* function,
similarly to our *requester* and *subscriber* functions. In this simple
example our UFEedClient instance acts to authenticate connecting
sessions from another client on the network:

```python
def authenticate(msg):
    # ...perform authentication work...
    return result

# use object in responder function
def responder_func(msg):
    if msg.longname == "RequestAuthenticate":
        return authenticate(msg)

# pass responder function to UFEedClient.start() function
uc.start(rep_func=responder_func)
```

Note that without a responder function defined, the `UFEed_Python` will do nothing with the messages it receives. That is, if other sessions are sending
requests to a `UFEed_Python` instance that does not have a responder function, they will not receive anything in reply.

## Publishing

The `UFEed_Python` manages its published messages via the `PUBLISHER` connection string, and its topic via the `PUBLISHER_TOPIC`. In this run-through example we are using the defaults (\"tcp://\*:55747\" and \"ufeedclient-publisher\") by not specifying them explicitly.

If we want to specify these values we define them in a dictionary:

```python
conn_strs = {PUBLISHER: 'tcp://*:55747',
             PUBLISHER_TOPIC: 'ufeedclient-publisher'}
```

and pass them to the UFEedClient at instantiation:

```python
uc = UFEedClient(conn_strs)
```

The `UFEed_Python` also has the ability to publish any type of message to any
number of subscribers, via the publish() function. In a case like this,
it may be important to enforce an interface for published messages.
Perhaps a published message will be expected to observe a very specific
format - maybe the programmer is creating a network of `UFEed_Python` clients, each
node with its own user, and wants to enforce consistency among them.

In this instance we are introduced to another aspect of `Message`
specialisation - enforcing required values. Such an interface would be
defined like:

```python
class MessageFactory:
    @staticmethod
    def create_status_notification(self, # define the required fields
                                   uc: UFEedClient,
                                   seq_num: int,
                                   status_id: str,
                                   status_msg: str,
                                   time: datetime = datetime.now()) -> Message.Builder:
        return uc.create_message() \
            .set_type(MsgType.st_system) \
            .set_long_name("status_notification") \
            .add_fields([
                (PRIVATE_SEQ_NUM, seq_num),
                (PRIVATE_STAT_ID, status_id),
                (PRIVATE_STAT_MSG, status_msg),
                (PRIVATE_TRANSACTTIME, transact_time)
            ])
```

It would then be used within the context of a script or Python program
like so:

```python
notification = MessageFactory.create_status_notification(uc, seq_num, status_id, status_msg)
uc.publish(notification)

# alternatively we could define a dictionary for our named arguments:
note = {"uc": uc,
        "seq_num": 1,
        "status_id": 0,
        "status_msg": "COMPLETE"}
notification = MessageFactory.create_status_notification(*note)
uc.publish(notification)
```

## Finishing Up

We have now successfully sent a *NewOrderSingle* message to the UFEGW,
and received a relevant Execution Report in response. We have also
learnt how to build `Message` specialisations to handle this Execution
Report in more specific, programmer-defined ways. We then learned about
the handling of requests to the `UFEed_Python` itself, and the `UFEed_Python`\'s ability to
publish messages to the broader network. In total, these requesting,
subscribing, responding and publishing actions encompass the 4-way
interface by which the `UFEed_Python` interacts with the UFEGW and also other
clients on the network.

To clean up our session, we will now log out, like so:

```python
logout = uc.create_message() \
    .set_long_name("logout") \
    .set_type(MsgType.st_system) \
    .set_service_id(UFE_CMD_LOGOUT) \
    .add_field(UFE_CMD, UFE_CMD_LOGOUT)
response = uc.request(logout)
```

# Message

The `UFEed_Python` can be used to send and receive any System or Business API
`Message` between itself and the UFEGW. The typical format of a printed
`Message` is:

```
# HEADER
name: "8"
longname: "ExecutionReport"
seq: 2889
service_id: 6

# FIELDS
fields {
location: fl_header
type: ft_string
tag: 35
sval: "8"
}
fields {
location: fl_header
type: ft_int
tag: 34
ival: 602
}
...
```

The creation of *Messages* can take 2 patterns:

```python
# 1. Recommended - create Message via a UFEedClient object
login = uc.create_message() \
    .set_long_name("login")
    .set_type(MsgType.st_system)
    .set_service_id(UFE_CMD_LOGIN) # MsgType.st_system means we are creating a SysMessage

# 2. !Outdated! - Create Message specifically, in this case a SysMessage (a FIXMessage would be defined using FIXMessage())
login = SysMessage.Builder()
login.longname = "login"
login.service_id = UFE_CMD_LOGIN

# Add relevant Message fields (can also be added as a list of tuple pairs [(a,b)(c,d)(e,f)] )
login.add_field(UFE_CMD, UFE_CMD_LOGIN) \
    .add_field(UFE_LOGIN_ID, "user01") \
    .add_field(UFE_LOGIN_PW, "password123456")

# Send the Message request, and capture the response
response = uc.request(login)
```
A message with groups can be created as (with generated FIX50 constants):

```python
fix50 = FIX50SP2_Fields

def test_message_with_groups():
    # simple test
    now = datetime.now()
    g1 = Message.Builder.GroupRef()
    g2 = Message.Builder.GroupRef()
    msg = FIXMessage.Builder() \
        .set_long_name("NewOrderSingle") \
        .set_name(fix50.MsgType.NEWORDERSINGLE) \
        .add_fields([(fix50.ClOrdID.tag, "123"),
                     (fix50.TransactTime.tag, now),
                     (fix50.ExecInst.tag, fix50.ExecInst.ALL_OR_NONE),
                     (fix50.TimeInForce.tag, fix50.TimeInForce.FILL_OR_KILL),
                     (fix50.Price.tag, 111.22),
                     (fix50.OrderQty.tag, 33),
                     (fix50.Side.tag, fix50.Side.BUY)]) \
        .add_field(fix50.OrdType.tag, fix50.OrdType.LIMIT) \
        .add_field(fix50.Account.tag, "ACC1") \
        .add_group(fix50.NoAllocs.tag, g1, lambda m, grp:
            m.add_group_item(g1)
                   .set_long_name("NoAlloc")
                   .set_type(MsgType.st_fixmsg)
                   .set_seq(1)
                   .add_field(fix50.AllocAccount.tag, "ALLOC1")
                   .add_field(fix50.AllocQty.tag, 50.) and
            m.add_group_item(g1)
                   .set_long_name("NoAlloc")
                   .set_type(MsgType.st_fixmsg)
                   .set_seq(3)
                   .add_field(fix50.AllocAccount.tag, "ALLOC2")
                   .add_field(fix50.AllocQty.tag, 60.)
                   ) \
        .add_field(UFE_SESSION_TOKEN, uuid.UUID("ed391284-bb68-4e14-a786-3eb0387694d9"), Location.fl_system) \
        .add_field(UFE_STATUS_CODE, Message.Status(1), Location.fl_system) \
        .add_field(fix50.PossDupFlag.tag, True) \
        .add_group(fix50.NoPartyIDs.tag, g1, lambda m, grp:
                m.add_group_item(grp)
                   .set_name(str(fix50.NoPartyIDs.tag))
                   .set_long_name("NoPartyIDs")
                   .set_type(MsgType.st_fixmsg)
                   .set_seq(1)
                   .add_field(fix50.PartyID.tag, "Party1")
                   .add_group(fix50.NoCapacities.tag, g2, lambda m, grp:
                        m.add_group_item(grp)
                              .set_name(str(fix50.NoCapacities.tag))
                              .set_long_name("NoCapacities")
                              .set_type(MsgType.st_fixmsg)
                              .set_seq(1)
                              .add_field(fix50.OrderQty.tag, 123)
                              )
                   ) \
        .build()
    print(msg)
```
UFEGW provides a vast array of System and Business API `Message`
interactivity. To further explore these functions, please refer to **4.
Implementation Guide - in particular sections 1.3 to 1.7**.

# Interface

## UFEedClient

The `UFEedClient` class is used as the interface to make both System and
Business API calls to the UFEGW. Sessions between `UFEedClient` and the
UFEGW are made up of ZeroMQ PUB/SUB and REQ/REP sockets. The network
addresses and message topics inherent to these sockets are configurable
via *UFEedClient.* In addition, the `UFEedClient` manages these UFEGW
sessions on behalf of the user (after the user has successfully logged
in).

The default instantiation of a `UFEedClient` object is expressed like
so:

```python
uc = UFEedClient()
```

Doing so will result in a `UFEedClient` object which utilises the
default connection string configuration. (These default values can be
found under *UFEGW CONNECTION STRINGS* in the consts.py file in section
1.6 below). If the user wishes to define these connection strings, they
can do so by passing a dictionary:

```python
conn_strs =    {
  "subscriber": "tcp://127.0.0.1:5000",
  "requester": "tcp://127.0.0.1:5001",
  "subscribertopic": "mygw-publisher"
}

uc = UFEedClient(conn_strs)
```

After a UFEedClient object has been created, it is in a ready state to connect to the UFEGW. In order to actually establish the connection, we call the start() function.

```python
uc.start()
# do work ...
uc.stop()
```

The `UFEedClient` will now go ahead and connect to the UFEGW. This means
it will actively receive published messages, and can make requests to
the UFEGW via the request() method. Note that by default uc.start() does
not do anything to specifically handle messages received from the UFEGW.
Oftentimes the user may wish to define a handling function that will
automatically be called when messages are received. A simple example
would be to print messages as they are received:

```python
def subscriber_func(msg):
    print(msg)

def responder_func(msg):
    print(msg)

uc.start(sub_func=subscriber_func, rep_func=responder_func)
# ...
uc.stop()
```

Another approach may be to store messages in a list automatically as
they are received, and do something with them later:

```python
submsgs = []
repmsgs = []

def subscriber_func(msg):
    submsgs.append(msg)

def responder_func(msg):
    repmsgs.append(msg)

uc.start(sub_func=subscriber_func, rep_func=responder_func)

# list comprehension calling do_something() on msg objects in repmsgs
res = [do_something(msg) for msg in repmsgs]

uc.stop()
```

The `UFEedClient` communicates with the UFEGW via *Messages* (see
section 1.5.2). In order to create a *Message,* the caller must specify
its header values, like so:

```python
# message often created with long name, message type and service id
service_list = uc.create_message() \
    .set_long_name("service_list") \
    .set_msg_type(MsgType.st_system) \
    .set_service_id(UFE_CMD_SERVICE_LIST) \
```

After a `Message` is created, the caller will add the necessary fields
for the body of the *Message:*

```python
service_list.add_field(UFE_CMD, UFE_CMD_SERVICE_LIST)
```

When the necessary fields have been added to the `Message`,
the caller may make a request() with the *Message.* (In this example the
caller has also decided to capture the response of this request in a
`Message` object called \"response\"):

```python
response = uc.request(service_list)
```

When the necessary fields have been added to the `Message` (see above),
the caller may make a publish() the `Message`:

```python
uc.publish(msg)
```
## Message and Message Builder

Message is built using \"builder\" pattern. Message.Builder class
provides write access to the message, while Message provides read-only
access to mapped message content, i.e. fields and groups.

```python
msg_builder = uc.create_message() \
    .set_name("abc") \
    .add_field(1, 2)
    ...
msg = msg_builder.build()
assert msg[1] == 2

msg.new_builder() \
    .add_field(2, "abc") \
    .build()
assert msg[1] == 2 and msg[2] = "abc"
```

The `Message` class provides some wrapping logic around the internal
WireMessage format utilised by the UFEGW. *Messages* are objects with
which requests are made from the UPA to the UFEGW. 

*Messages* can be created via the `UFEedClient` create_message()
function (see section 1.5.1 above). For example, a NewOrderSingle
message:

```python
# recommended
nos = uc.create_message() \
    .set_long_name("NewOrderSingle") \
    .set_name("D") \
    .set_type(MsgType.st_fixmsg) \
    .set_service_id(6) # service id is 6
```

Or created directly:

```python
# !outdated!
login = SysMessage()
login.longname = "login"
login.service_id = UFE_CMD_LOGIN
```

The add_group()/add_group_item() methods allow the caller to add groups
and group content to the `Message`:

```python
g1 = Message.Builder.GroupRef()
msg.add_group(fix50.NoAllocs.tag, g1, lambda m, grp:
            m.add_group_item(g1)
                   .set_long_name("NoAlloc")
                   .set_type(MsgType.st_fixmsg)
                   .set_seq(1)
                   .add_field(fix50.AllocAccount.tag, "ALLOC1")
                   .add_field(fix50.AllocQty.tag, 50.) and
```

Expose the underlying WireMessage stored in the `Message` object:

```python
wm = msg.wire_message
```

`Message` objects are provide a printable internal representation (via
*\_\_repr\_\_* and *\_\_str\_\_*):

```
print(msg)
```

Creates an immutable Message with mapped fields and groups. Searching by
tag is available via \[ \]

```python
msg = uc.create_message() \
    .set_type(MsgType.st_fix) \
    .set_long_name("NewOrderSingle") \
    .set_name(fix50.MsgType.NEWORDERSINGLE) \
    .add_fields([(fix50.ClOrdID.tag, "123"), (fix50.TransactTime.tag, now)])
    .build()
assert msg[fix50.ClOrdID.tag] == "123"
assert msg[fix50.OrderID.tag] is None
```

# Constants

The UPA maintains a list of constant values that translate to integer
codes in the UFEGW. These integer codes are used to identify System API
services as well as general FIX functionality. Constants could be regenerated
via `consts_gen.py`. Some examples of the use of these codes in the above examples are:

```python
service_list.add_field(UFE_CMD, UFE_CMD_SERVICE_LIST)
```
and
```python
nos.add_fields([
    (COMMON_SYMBOL, "BHP"), 
    (COMMON_CLORDID, "Ord01"), 
    (COMMON_ORDERQTY, 100.), 
    (COMMON_PRICE, 10.25), 
    (COMMON_ORDTYPE, '1'), 
    (COMMON_SIDE, '0'), 
    (COMMON_TIMEINFORCE, '2'), 
    (COMMON_TRANSACTTIME, "now")])
```
A full list of these constants is available at `consts.py`.

## FIX variants constants

The UPA provides constants for all stock FIX variants:

```python
# FIX50SP2 NOS creation
fix42 = FIX42_Fields
fix50 = FIX50SP2_Fields

def create_fix50_nos():
    now = datetime.now()
    g1 = Message.Builder.GroupRef()
    g2 = Message.Builder.GroupRef()
    nos = uc.create_message() \
        .set_type(MsgType.st_fix) \
        .set_long_name("NewOrderSingle") \
        .set_name(fix50.MsgType.NEWORDERSINGLE) \
        .add_fields([(fix50.ClOrdID.tag, "123"),
                     (fix50.TransactTime.tag, now),
                     (fix50.ExecInst.tag, fix50.ExecInst.ALL_OR_NONE),
                     (fix50.TimeInForce.tag, fix50.TimeInForce.FILL_OR_KILL),
                     (fix50.Price.tag, 111.22),
                     (fix50.OrderQty.tag, 33),
                     (fix50.Side.tag, fix50.Side.BUY)]) \
        .add_field(fix50.OrdType.tag, fix50.OrdType.LIMIT) \
        .add_field(fix50.Account.tag, "ACC1") \
        .add_group(fix50.NoAllocs.tag, g1, lambda m, grp:
            m.add_group_item(g1)
                   .set_long_name("NoAlloc")
                   .set_type(MsgType.st_fixmsg)
                   .set_seq(1)
                   .add_field(fix50.AllocAccount.tag, "ALLOC1")
                   .add_field(fix50.AllocQty.tag, 50.) and
            m.add_group_item(g1)
                   .set_long_name("NoAlloc")
                   .set_type(MsgType.st_fixmsg)
                   .set_seq(3)
                   .add_field(fix50.AllocAccount.tag, "ALLOC2")
                   .add_field(fix50.AllocQty.tag, 60.)
                   )
    return nos
```

# Logging

In order to generate a debug log, the UPA requires a file called
\"upa.log\" to be present in the root directory from which the UPA is
run. If this file is present, the UPA knows to sink debug messages into
this file during its execution. If the file is not present, the UPA will
not execute any logging function.

Be careful to ensure this file is not present when you do not wish to
capture logs; the UPA will have better performance when not executing
any logging functions.

