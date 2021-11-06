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
from typing import Optional

import pytest

from UPA import *
import re
import time


class Env:
    def __init__(self, conn_strs):
        # SETUP / TESTING
        self._uc = UFEedClient(conn_strs)

        # setup capture list to capture subscriber messages
        self._capture: [Message] = []

    # define function which reflects message back for reply function
    def _request_func(self, msg: Message) -> None:
        pass

    def _reflect_request(self, msg: Message) -> Message:
        return msg

    def _sub_capture(self, msg: Message):
        self._capture.append(msg)

    @property
    def ufeedclient(self):
        return self._uc

    @property
    def captured_messages(self) -> [Message]:
        return self._capture

    @captured_messages.setter
    def captured_messages(self, msgs: [Message]) -> None:
        self._capture = msgs

    def connect(self):
        # start the client
        self._uc.start(sub_func=self._sub_capture, req_func=self._request_func, rep_func=self._reflect_request)

    def disconnect(self):
        self._uc.stop()

    def generate_logon(self, user: str = "webuser", passw: str = "pass") -> Message.Builder:
        return self._uc.create_message() \
            .set_long_name("login") \
            .set_type(MsgType.st_system) \
            .set_service_id(UFE_CMD_LOGIN) \
            .add_field(UFE_CMD, UFE_CMD_LOGIN) \
            .add_field(UFE_LOGIN_ID, user) \
            .add_field(UFE_LOGIN_PW, passw)


# _local_env is a test environment that connects to itself w/o external UFEGW app
# set UFEedClient connection strings to point to each other
_local_env: Optional[Env] = None
ENABLE_UGEGW_TESTS = False


@pytest.fixture()
def local_env_setup():
    # setup
    global _local_env
    _local_env = Env(conn_strs={SUBSCRIBER: 'tcp://127.0.0.1:55747',
                                SUBSCRIBER_TOPIC: 'ufeedclient-publisher',
                                REQUESTER: 'tcp://127.0.0.1:55748',
                                REQUESTER_TOPIC: 'ufeedclient-responder'})
    try:
        _local_env.connect()
        yield
    finally:
        # teardown
        _local_env.disconnect()
        del _local_env


# TESTS
@pytest.mark.usefixtures('local_env_setup', scope='session')
@pytest.mark.timeout(20)
def test_local_req_rep():
    uc = _local_env.ufeedclient
    msg = _local_env.generate_logon()
    msg_rep = uc.request(msg)
    assert str(msg.build()) == str(msg_rep)


@pytest.mark.usefixtures('local_env_setup', scope='session')
@pytest.mark.timeout(20)
def test_local_pub_sub():
    uc = _local_env.ufeedclient
    _local_env.captured_messages.clear()
    msg = uc.create_message().set_long_name("Test").set_type(MsgType.st_system).set_service_id(1)
    # first X message will be skipped due to subscription setup process
    for i in range(100):
        uc.publish(msg)
        time.sleep(0.001)
    # subscriber receipt is caught in capture list
    assert len(_local_env.captured_messages) > 0
    assert str(msg.build()) == str(_local_env.captured_messages[0])


@pytest.mark.usefixtures('local_env_setup', scope='session')
@pytest.mark.timeout(60)
def test_local_load_pub_sub():
    uc = _local_env.ufeedclient
    _local_env.captured_messages.clear()
    msgs = [uc.create_message().set_long_name("Test").set_type(MsgType.st_system).set_service_id(i) for i in range(1, 100001)]
    for msg in msgs:
        uc.publish(msg)
    time.sleep(1)
    assert len(_local_env.captured_messages) >= len(msgs) - len(msgs) * 0.1 # possible loss of fist X messages

