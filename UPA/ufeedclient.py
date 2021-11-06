# --------------------------------------------------------------------------------------------
#    ____                      __      ____
#   /\  _`\   __             /'_ `\   /\  _`\
#   \ \ \L\_\/\_\    __  _  /\ \L\ \  \ \ \L\ \ _ __    ___
#    \ \  _\/\/\ \  /\ \/'\ \/_> _ <_  \ \ ,__//\`'__\ / __`\
#     \ \ \/  \ \ \ \/>  </   /\ \L\ \  \ \ \/ \ \ \/ /\ \L\ \
#      \ \_\   \ \_\ /\_/\_\  \ \____/   \ \_\  \ \_\ \ \____/
#       \/_/    \/_/ \//\/_/   \/___/     \/_/   \/_/  \/___/
#
#                     Universal FIX Engine
#
# Copyright (C) 2017-19 Fix8 Market Technologies Pty Ltd (ABN 29 167 027 198)
# All Rights Reserved. [http://www.fix8mt.com] <heretohelp@fix8mt.com>
#
# THIS FILE IS PROPRIETARY AND  CONFIDENTIAL. NO PART OF THIS FILE MAY BE REPRODUCED,  STORED
# IN A RETRIEVAL SYSTEM,  OR TRANSMITTED, IN ANY FORM OR ANY MEANS,  ELECTRONIC, PHOTOSTATIC,
# RECORDED OR OTHERWISE, WITHOUT THE PRIOR AND  EXPRESS WRITTEN  PERMISSION  OF  FIX8  MARKET
# TECHNOLOGIES PTY LTD.
#
# --------------------------------------------------------------------------------------------
import atexit
import hashlib
import logging
import os
import threading
import time
from typing import Optional

import zmq

from UPA.consts import *
from UPA.message import *

if not os.path.isfile('upa.log'):
    upa_logging = False
else:
    upa_logging = True
    logging.basicConfig(filename='upa.log',
                        format='%(asctime)s.%(msecs)03d %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)


def log(func):
    if not upa_logging:
        return func

    def function_wrapper(*args, **kwargs):
        logging.info(f"{func} START")
        res = func(*args, **kwargs)
        logging.info(f"{func} END")
        return res

    return function_wrapper


class UFEedClient:
    """The UFEedClient object manages requests, responses, publishing and subscriptions for all Messages from the UFEGW and other UFEedClients.
    
    Raises:
        LookupError: If there is an attempt to make a request before a login session ID has been established
                     a LookupError will be thrown.
    
    Returns:
        UFEedClient: The UFEedClient object.
    """

    # prepares connection strings, sockets and session_id
    @log
    def __init__(self, connection_string_dict=None):
        if connection_string_dict is None:
            connection_string_dict = {}
        self.__cs = self.__set_connection_strings(connection_string_dict)
        self.__context = zmq.Context()
        self.__req_socket = self.__context.socket(zmq.REQ)
        self.__pub_socket = self.__context.socket(zmq.PUB)
        self.__stop_threads = False
        self.__stop_responder_thread = False
        self.__sub_thread: threading.Thread = threading.Thread()
        self.__rep_thread: Optional[threading.Thread] = None
        self.__session_id = None  # session id
        self.started = False
        self.sub_handlers: List[Callable[[Message], None]] = []  # prepare handler functions
        self.req_handlers: List[Callable[[Message], None]] = []
        self.rep_handlers: List[Callable[[Message], Message]] = []

        atexit.register(self.__cleanup)

    @log
    def __str__(self):
        """When cast to a str object, UFEedClient serialises its connection string details.
        
        Returns:
            str: connection strings
        """
        return ",".join(("{}={}".format(*i) for i in self.__cs.items()))

    # destructor, logs out, cleans up session id, shuts down threads
    @log
    def __cleanup(self, do_not_send_logout = False) -> None:
        if self.started:
            if not do_not_send_logout and self.__session_id:
                logout = self.create_message() \
                    .set_long_name("logout") \
                    .set_type(MsgType.st_system) \
                    .set_service_id(UFE_CMD_LOGOUT) \
                    .add_field(UFE_CMD, Message.Status(UFE_CMD_LOGOUT))
                self.request(logout)
            self.__close_all_sockets()
        self.__session_id = None
        self.__stop_threads = True
        self.__stop_responder_thread = True
        self.__sub_thread.join(1)
        if self.__rep_thread:
            self.__rep_thread.join()

    # repurposes existing REQ and PUB sockets to flush REP and SUBs on threads
    # after this function is called, REQ, REP, PUB and SUB sockets are all closed
    # (protected)
    @log
    def __close_all_sockets(self) -> None:
        print("closing sockets...")

        if self.__req_socket is None and self.__pub_socket is None:
            print("sockets already closed...")
            return

        pub_endpoint = self.__pub_socket.get(zmq.LAST_ENDPOINT)
        self.__pub_socket.unbind(pub_endpoint)
        sub_loopback_port = self.__cs[SUBSCRIBER].split(':')[2]
        sub_loopback_address = f"tcp://127.0.0.1:{sub_loopback_port}"

        req_endpoint = self.__req_socket.get(zmq.LAST_ENDPOINT)
        self.__req_socket.unbind(req_endpoint)
        rep_loopback_port = self.__cs[RESPONDER].split(':')[2]
        rep_loopback_address = f"tcp://127.0.0.1:{rep_loopback_port}"

        # give sockets time to unbind
        time.sleep(1)

        self.__pub_socket.connect(sub_loopback_address)
        self.__req_socket.connect(rep_loopback_address)

        # give sockets time to connect
        time.sleep(1)

        self.__req_socket.send("".encode(), zmq.SNDMORE)
        self.__req_socket.send("".encode())
        self.__pub_socket.send(self.__cs[SUBSCRIBER_TOPIC].encode(), zmq.SNDMORE)  # TODO:
        self.__pub_socket.send("".encode())

        self.__req_socket.close()
        self.__pub_socket.close()
        self.__req_socket = None
        self.__pub_socket = None

    # prepares dictionary of connection strings (protected)
    @log
    def __set_connection_strings(self, d: {str, str}) -> {str, str}:
        conn_strs = {}
        conn_strs[SUBSCRIBER] = d.get(SUBSCRIBER, SUBSCRIBER_DEFAULT)
        conn_strs[REQUESTER] = d.get(REQUESTER, REQUESTER_DEFAULT)
        conn_strs[PUBLISHER] = d.get(PUBLISHER, PUBLISHER_DEFAULT)
        conn_strs[RESPONDER] = d.get(RESPONDER, RESPONDER_DEFAULT)
        conn_strs[SUBSCRIBER_TOPIC] = d.get(SUBSCRIBER_TOPIC, SUBSCRIBER_TOPIC_DEFAULT)
        conn_strs[REQUESTER_TOPIC] = d.get(REQUESTER_TOPIC, REQUESTER_TOPIC_DEFAULT)
        conn_strs[PUBLISHER_TOPIC] = d.get(PUBLISHER_TOPIC, PUBLISHER_TOPIC_DEFAULT)
        conn_strs[RESPONDER_TOPIC] = d.get(RESPONDER_TOPIC, RESPONDER_TOPIC_DEFAULT)
        return conn_strs

    # WireMessage submitted for REQ/REP, returns resultant WireMessage (protected)
    @log
    def __request_response(self, wm: WireMessage) -> WireMessage:
        wms = wm.SerializeToString()
        self.__req_socket.send(self.__cs[REQUESTER_TOPIC].encode(), zmq.SNDMORE)
        self.__req_socket.send(wms)
        response = self.__req_socket.recv_multipart()[1]
        wm_r = WireMessage()
        wm_r.ParseFromString(response)
        return wm_r

    # responder socket gets popped out to separate thread but shares context with main thread (protected)
    @log
    def __poll_responder(self) -> None:
        rep_socket = self.__context.socket(zmq.REP)
        rep_socket.bind(self.__cs[RESPONDER])

        while True:
            msg = rep_socket.recv_multipart()
            if self.__stop_responder_thread:
                break
            elif msg[0].decode('utf-8') != self.__cs[RESPONDER_TOPIC]:
                sss = msg[0].decode('utf-8')
                rep_socket.send("".encode(), zmq.SNDMORE)
                rep_socket.send("TOPIC UNKNOWN".encode())
            else:
                msg1 = msg[1]
                wm = WireMessage()
                wm.ParseFromString(msg1)
                msg2: Optional[Message] = None
                for f in self.rep_handlers:
                    msg2 = f(self.create_message(wm).build())
                rep_socket.send(self.__cs[RESPONDER_TOPIC].encode(), zmq.SNDMORE)
                rep_socket.send(msg2.wire_message.SerializeToString())

        rep_socket.close()

    # subscriber socket gets popped out to separate thread but shares context with main thread (protected)
    @log
    def __poll_subscriber(self):
        sub_socket = self.__context.socket(zmq.SUB)
        sub_socket.setsockopt(zmq.SUBSCRIBE, self.__cs[SUBSCRIBER_TOPIC].encode())
        sub_socket.connect(self.__cs[SUBSCRIBER])

        while True:
            msg = sub_socket.recv_multipart()[1]
            if self.__stop_threads:
                break
            else:
                wm = WireMessage()
                wm.ParseFromString(msg)
                for f in self.sub_handlers:
                    f(self.create_message(wm).build())

        sub_socket.close()

    # password hashing function, currently unused (protected)
    @log
    def __hash_password(self, wm):
        pw_field = [field for field in wm.fields if field.tag == UFE_LOGIN_PW][0]
        pw = pw_field.sval
        sha256 = hashlib.sha256()
        sha256.update(pw)
        pw = sha256.hexdigest()
        pw_field.sval = pw.encode()

        return wm

    # default handler function (protected)
    @log
    def __pass(self):
        pass

    @log
    def create_message(self, wm: WireMessage = None) -> Message.Builder:
        """Factory function to create a SysMessage or FIXMessage.
        
        Args:
            wm (WireMessage, optional): optional WireMessage object to create a Message.Builder from
        
        Returns:
            Message.Builder: message builder to build the message
        """
        return Message.Builder(wm)

    @log
    def publish(self, msg: Message.Builder):
        """Publishes Messages to UFEedClient subscribers.
        
        Args:
            msg (Message.Builder): Message to be published.
        """
        self.__pub_socket.send(self.__cs[PUBLISHER_TOPIC].encode(), zmq.SNDMORE)
        self.__pub_socket.send(msg.wire_message.SerializeToString())

    # handles REQ/REP, autopopulates session token if necessary, throws if no session token and not login attempt
    @log
    def request(self, msg: Message.Builder) -> Message:
        """Handles request/response loop for Messages sent to and received from the UFEGW.
        
        Args:
            msg (Message.Builder): Message to be sent via request.
        
        Raises:
            LookupError: If there is an attempt to make a request before a login session ID has been established
                         a LookupError will be thrown.
        
        Returns:
            Message: Message received via response.
        """

        # have we already logged in?
        if self.__session_id and msg.service_id != UFE_CMD_LOGOUT:
            # avoid msg.add_fields() for speed - (could also hardcode location and type)
            msg.add_field(UFE_SESSION_TOKEN, self.__session_id, Location.fl_system)
            wm = self.__request_response(msg.wire_message)

        # well ok, is this a login attempt?
        elif msg.service_id == UFE_CMD_LOGIN:
            # wm = self.__hash_password(wm)
            wm = self.__request_response(msg.wire_message)
            session_field = [field for field in wm.fields if field.tag == UFE_SESSION_TOKEN]
            if session_field:
                self.__session_id = uuid.UUID(bytes=session_field[0].sval)

        # logging out?
        elif msg.service_id == UFE_CMD_LOGOUT:
            msg.add_field(UFE_SESSION_TOKEN, self.__session_id, Location.fl_system)
            wm = self.__request_response(msg.wire_message)
            logged_off = [field for field in wm.fields if field.tag == UFE_RESPONSE_CODE]
            if logged_off and logged_off[0].ival == LOGOFF_SUCCESSFUL:
                self.__session_id = None

        # neither?
        else:
            raise LookupError('No session token found - you must log on before making a request.')

        # send REP WireMessage to REQ handler function
        msg = self.create_message(wm).build()
        for f in self.req_handlers:
            f(msg)
        return msg

    @log
    def start(self, sub_func, req_func, rep_func=None):
        """The start() function must be invoked in order for the UFEedClient to begin interaction with the UFEGW.

        Args:
            sub_func (def()): The subscriber Message handling function. Must be defined.
            req_func (def()): The request Message handling function. Must be defined.
            rep_func (def()): The response Message handling function. Defaults to "pass".
        """
        self.add_sub_handler(sub_func)  # prepare handler functions
        self.add_req_handler(req_func)
        if rep_func is not None:
            self.add_rep_handler(rep_func)
        self.__req_socket.connect(self.__cs[REQUESTER])  # start REQ
        self.__pub_socket.bind(self.__cs[PUBLISHER])  # start PUB
        self.__sub_thread = threading.Thread(target=self.__poll_subscriber, daemon=True)  # SUB in daemon thread
        self.__sub_thread.start()
        self.started = True

    @log
    def stop(self, do_not_send_logout = False) -> None:
        """ Stops UFEedClient and cleans up taken resources: sockets, threads, etc """
        self.__cleanup(do_not_send_logout)
        self.started = False

    @log
    def __del__(self):
        self.stop()

    @log
    def add_sub_handler(self, sub_func: Callable[[Message], None]):
        self.sub_handlers.append(sub_func)

    @log
    def remove_sub_handler(self, sub_func: Callable[[Message], None]):
        self.sub_handlers.remove(sub_func)

    @log
    def add_req_handler(self, req_func: Callable[[Message], None]):
        self.req_handlers.append(req_func)

    @log
    def remove_req_handler(self, req_func: Callable[[Message], None]):
        self.req_handlers.remove(req_func)

    @log
    def add_rep_handler(self, rep_func: Callable[[Message], Message]):
        self.rep_handlers.append(rep_func)
        if len(self.rep_handlers) == 1:
            self.__rep_thread = threading.Thread(target=self.__poll_responder, daemon=True)  # REP in daemon thread
            self.__rep_thread.start()

    @log
    def remove_rep_handler(self, rep_func: Callable[[Message], Message]):
        self.rep_handlers.remove(rep_func)
        if len(self.rep_handlers) == 0 and self.__rep_thread is not None:
            self.__stop_responder_thread = True
            self.__rep_thread.join(1)
            self.__rep_thread = None
