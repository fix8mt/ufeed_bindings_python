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
from _signal import SIGTERM, SIGKILL
from time import sleep

import pytest
import redis
import psutil
#import hiredis
import subprocess

from UPA.ufegwclient import *  # todo: move that import to UPA.__init__ when ready


class Env:
    OS_ENV_KEY = "FIX8PRO_ENABLE_UGEGW_TESTS"
    OS_ENV_UFEGW_ROOT = "FIX8PRO_UFEGW_ROOT"
    OS_ENV_FIX8PRO_ROOT = "FIX8PRO_ROOT"
    OS_ENV_FIX8PRO_LICENSE_FILE = "FIX8PRO_LICENSE_FILE"
    UFEGW_LICENSE = os.environ.get(OS_ENV_FIX8PRO_LICENSE_FILE, "/home/sergey/src/f8/f8pro-all.license")
    SKIP_UGEGW_TESTS = int(os.environ.get(OS_ENV_KEY, 1)) == 0
    UFEGW_ROOT = os.environ.get(OS_ENV_UFEGW_ROOT, "/home/sergey/src/f8/ufegw/cmake-build-debug")
    FIX8PRO_ROOT = os.environ.get(OS_ENV_FIX8PRO_ROOT, "/home/sergey/src/f8/fix8pro/cmake-build-debug")
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    TEST_SUITE_NAME = "ufegw_test_suite"
    TEST_SKIP_MESSAGE = f"to run tests: export {OS_ENV_KEY}=1 {OS_ENV_UFEGW_ROOT}=<ufegw path> {OS_ENV_FIX8PRO_ROOT}=<f8ptest path> {OS_ENV_FIX8PRO_LICENSE_FILE}=<fix8pro license path>"
    CONFIG_ROOT = "UFEGWTestSuite"
    CONFIG_MIDDLEWARE_PORT_PUBLISHER = 55745
    CONFIG_MIDDLEWARE_PORT_RESPONDER = 55746
    CONFIG_MIDDLEWARE_PORT_REQUESTER = 55748
    CONFIG_MIDDLEWARE_PORT_REQUESTER_RPC = 55748    # same as CONFIG_MIDDLEWARE_PORT_REQUESTER
    CONFIG_MIDDLEWARE_TOPIC01_REQUESTER_RPC = RESPONDER_TOPIC_DEFAULT #"rpc_request_01" same as RESPONDER_TOPIC_DEFAULT
    CONFIG_ALL_USERS = """<?xml version="1.0" encoding="ISO-8859-1"?>
<fix8>
    <ufegw>
        <users hash="sha256">
            <user id="admin" pw="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8" services="*"/>
            <user id="webuser" pw="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8" services="1,2,3,4,5,6" viewonly="true"/>
        </users>
    </ufegw>
</fix8>"""
    CONFIG_ALL_SESSION_DEFAULTS = f"""<?xml version='1.0' encoding='ISO-8859-1'?>
<fix8>
    <default role="acceptor" fix_version="1100" ip="127.0.0.1" session_log="session_log_file" protocol_log="protocol_log_file"
                login_retry_interval="1000" reset_sequence_numbers="false" default_appl_ver_id="9" connect_timeout="3" heartbeat_interval="10"
                tcp_nodelay="true" always_seqnum_assign="false" process_model="coroutime" enforce_compids="false" login_retries="0" tabsize="3"
                ipersist="file1" persist="file0" />
    <persist name="file0" type="file" dir="./run_{TEST_SUITE_NAME}" use_session_id="true" rotation="5" db="client" />
    <persist name="file1" type="file" dir="./run_{TEST_SUITE_NAME}" use_session_id="true" rotation="5" db="iclient" />
    <persist name="file2" type="file" dir="./run_{TEST_SUITE_NAME}" rotation="5" db="svpclient" /> 
    <persist name="redis0" type="hiredis" host="127.0.0.1" port="6379" connect_timeout="1" db="svptest" />
    <log name="session_log_file" type="file" filename="./run_{TEST_SUITE_NAME}/ufegw_session.log" rotation="5" flags="timestamp|sequence|level|thread"/>
    <log name="protocol_log_file" type="file" filename="./run_{TEST_SUITE_NAME}/ufegw_protocol.log" rotation="5" flags="append|inbound|outbound|direction|sequence"/>
</fix8>"""
    CONFIG_TRANSFORM_RPC_ALL = f"""
                <transform value0="timeout" value1="retry" value2="topic" value3="endpoint">
                   <field location="all" policy="rpc" tags="*" timeout="3" retry="3" topic="{CONFIG_MIDDLEWARE_TOPIC01_REQUESTER_RPC}" endpoint="tcp://127.0.0.1:{CONFIG_MIDDLEWARE_PORT_REQUESTER_RPC}" direction="both"/>
                </transform>"""
    CONFIG_MAIN = f"""<?xml version="1.0" encoding="ISO-8859-1"?>
<fix8>
    <session name="SS8I" role="initiator" sender_comp_id="YYI8_XXA8" target_comp_id="XXA8_YYI8" port="11088" active="true" persist="file0" reset_sequence_numbers="true"/>
    <session name="SS8A" role="acceptor"  sender_comp_id="YYA8_XXI8" target_comp_id="XXI8_YYA8" port="11078" active="true" persist="file0"/>
    <ufegw name="{CONFIG_ROOT}" workers="5" middleware="test01" polltimeoutms="10" maxmsgsperworkerloop="25" subscriberroottopic="ufegw-publisher" requestertopic="ufegw-requester" respondertopic="ufegw-responder" ufeedlog="ufeed">
        <suppress>
            <field location="trailer" tag="10" COMMENT="chksum" />
            <field location="header" tag="9" COMMENT="msglen" />
            <field location="header" tag="8" COMMENT="beginstring" />
            <field location="header" tag="49" COMMENT="sendercompid" />
            <field location="header" tag="56" COMMENT="targetcompid" />
        </suppress>
        <profiles report="true" txadmin="true" servicelogging="false" giveupreset="21" role="initiator" config="this" sessiondefaults="persist://{CONFIG_ROOT}/AllSessionDefaults">
            <profile name="SS8A" role="acceptor" ns="FIX50SP2" serviceid="8" servicetag="ss-8i" giveupreset="10">
                <authenticate rejectonerror="false"/>
            </profile>
            <profile name="SS8I" role="initiator" ns="FIX50SP2" serviceid="9" servicetag="ss-8a" giveupreset="10">
                <authenticate rejectonerror="false"/>
            </profile>
        </profiles>
        <users pwhash="sha256" config="persist://{CONFIG_ROOT}/AllUsers" />
    </ufegw>
    <middleware name="test01" type="zmq" publisher="tcp://*:{CONFIG_MIDDLEWARE_PORT_PUBLISHER}" responder="tcp://*:{CONFIG_MIDDLEWARE_PORT_RESPONDER}" requester="tcp://localhost:{CONFIG_MIDDLEWARE_PORT_REQUESTER}">
        <parameters server="true" poll_interval_ms="10" iothreads="1" />
    </middleware>
    <log name="ufeed" type="ufeedfile" filename="./run_{TEST_SUITE_NAME}/ufeed.log" rotation="5" flags="timestamp|inbound|outbound|direction|thread|sequence" translate="true"/>
</fix8>"""
    CONFIG_MAIN_IDX = "AllSessionDefaults\nAllUsers"
    CONFIG_MINIMAL = f"""<?xml version="1.0" encoding="ISO-8859-1"?>
<fix8>
    <ufegw persist="redis0"/>
    <persist name="redis0" type="hiredis" host="{REDIS_HOST}" port="{REDIS_PORT}" connect_timeout="1" db="{TEST_SUITE_NAME}" />
    <persist name="file2" type="file" dir="./db" rotation="5" db="{TEST_SUITE_NAME}e" />
</fix8>"""
    CONFIG_CLIENT_MINIMAL = """
    <default role="initiator" fix_version="1100" ip="127.0.0.1" session_log="session_log_file" protocol_log="protocol_log_file" login_retry_interval="4000"
        reset_sequence_numbers="false" connect_timeout="3" default_appl_ver_id="8" heartbeat_interval="10" tcp_nodelay="true" always_seqnum_assign="false"
        process_model="threaded" enforce_compids="false" login_retries="5" tabsize="3" persist="file0" />
    <persist name="redis0" type="hiredis" host="127.0.0.1" port="6379" connect_timeout="1" db="svptest" />
    <persist name="file0" type="file" dir="./run_client" use_session_id="true" rotation="5" db="client" />
    <log name="session_log_file" type="file" filename="./run_client/myfix_client_session.log" rotation="5" levels="debug|info|warn|error|fatal" flags="sequence|timestamp|sstart|thread|location|level"/>
    <log name="protocol_log_file" type="file" levels="debug|info|warn|error|fatal" filename="./run_client/myfix_client_protocol.log" rotation="5" flags="sequence|append|direction|inbound|outbound"/>
"""
    CONFIG_CLIENT = f"""<?xml version='1.0' encoding='ISO-8859-1'?>
<fix8>
    {CONFIG_CLIENT_MINIMAL}
    <session name="SS8I" role="initiator" sender_comp_id="XXI8_YYA8" target_comp_id="YYA8_XXI8" port="11078" active="true" persist="file0" reset_sequence_numbers="true"/>
    <session name="SS8A" role="acceptor" sender_comp_id="XXA8_YYI8" target_comp_id="YYI8_XXA8" port="11088" active="true" persist="file0"/>
    <session name="SS9I" role="initiator" sender_comp_id="XXI9_YYA9" target_comp_id="YYA9_XXI9" port="11019" active="true" persist="file0" reset_sequence_numbers="true"/>
    <session name="SS9A" role="acceptor" sender_comp_id="XXA9_YYI9" target_comp_id="YYI9_XXA9" port="11099" active="true" persist="file0"/>
</fix8>"""
    TMP_DIR = f".{TEST_SUITE_NAME}"

    def __init__(self, conn_strs: dict):
        # SETUP / TESTING
        self._uc = UFEGWClient(conn_strs)
        self._session_token: Optional[UUID] = None
        self._cp: Optional[subprocess.Popen] = None
        self._redis: redis.Redis = redis.Redis(host=Env.REDIS_HOST, port=Env.REDIS_PORT, decode_responses=True)
        self.current_user: Optional[str] = None
        self._start_process: bool = True
        for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            if Env.CONFIG_ROOT in proc.cmdline():
                self._start_process = False
                break
        os.makedirs(Env.TMP_DIR, exist_ok=True)
        os.chdir(Env.TMP_DIR)
        if self._start_process:
            self.load_initial_config()
            self.start_ufegw_process()

    @property
    def ufegw_client(self):
        return self._uc

    @property
    def session_token(self) -> UUID:
        return self._session_token

    @session_token.setter
    def session_token(self, session_token):
        self._session_token = session_token

    def _empty_handler(self, msg: Message) -> None:
        pass

    def connect(self):
        # start the client
        self._uc.start(sub_func=self._empty_handler, req_func=self._empty_handler, rep_func=None)
        status, session_token = self._uc.logon(user="webuser", passw="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8")
        assert session_token is not None
        assert status == Message.Status(LOGIN_ACCEPTED)
        self._session_token = session_token

    def disconnect(self):
        if self._uc is None: # already stopped
            return
        if self._uc.started and self._session_token is not None:
            status = self._uc.logout()
            assert status.status == LOGOFF_SUCCESSFUL or status.status == NOT_LOGGED_IN
        self._uc.stop(do_not_send_logout=True)

    def add_sub_handler(self, sub_func):
        self._uc.add_sub_handler(sub_func)

    def add_req_handler(self, req_func):
        self._uc.add_req_handler(req_func)

    def add_rep_handler(self, rep_func):
        self._uc.add_rep_handler(rep_func)

    def load_initial_config(self):
        file_kv = [("ufegw_minimal.xml", Env.CONFIG_MINIMAL), ("f8ptest.xml", Env.CONFIG_CLIENT)]
        cfg_kv = [("", Env.CONFIG_MAIN), ("/AllUsers", Env.CONFIG_ALL_USERS), ("/AllSessionDefaults", Env.CONFIG_ALL_SESSION_DEFAULTS), (".idx", Env.CONFIG_MAIN_IDX)]
        for k in self._redis.keys(f"{Env.TEST_SUITE_NAME}*"):
            self._redis.delete(k)
        assert len(self._redis.keys(f"{Env.TEST_SUITE_NAME}*")) == 0
        for k, v in file_kv:
            with open(k, "w") as f:
                f.writelines(v)
        for k, v in cfg_kv:
            self._redis.set(f"{Env.TEST_SUITE_NAME}/{Env.CONFIG_ROOT}{k}", v)
            s = self._redis.get(f"{Env.TEST_SUITE_NAME}/{Env.CONFIG_ROOT}{k}")
            assert s == v
            with open(f"{Env.TEST_SUITE_NAME}_{k.replace('/', '-').replace('.', '_')}.xml", "w") as f:
                f.writelines(v)

    def load_profile(self, key: str, value: str):
        #self._redis.set(f"{Env.TEST_SUITE_NAME}/{Env.CONFIG_ROOT}/{key}", value)
        current_user = self.current_user
        if current_user != "admin":
            self.logout_and_logon_as_admin()
        assert self.current_user == "admin"
        config_list: UFEGWConfigList
        status, config_list = self._uc.config_list(force_refresh=True)
        assert status.status == UFE_OK
        conf = config_list[UFE_CONFIG_MAINCFG_TAG]
        status, prf = config_list.put(UFEGWConfig(name=f"{conf.name}/{key}", rec=value), UFEGWConfigList.CommitAction.COMMIT_REPLACE_AND_LOAD)
        assert status.status == UFE_OK
        assert prf.name == f"{conf.name}/{key}"
        if current_user != "admin":
            self.logout_and_logon_as_user()

    def drop_config(self, key: str):
        self._redis.delete(f"{Env.TEST_SUITE_NAME}/{Env.CONFIG_ROOT}/{key}")

    def start_ufegw_process(self):
        self._cp = subprocess.Popen([f"{Env.UFEGW_ROOT}/ufegw", "-Dc", "ufegw_minimal.xml", Env.CONFIG_ROOT], cwd=os.getcwd(),
                                  env={Env.OS_ENV_FIX8PRO_LICENSE_FILE: Env.UFEGW_LICENSE})
        assert self._cp.pid != 0
        assert self._cp.returncode is None

    def stop_ufegw_process(self):
        is_running = self._cp.poll()
        if is_running is None:
            self._uc.stop(do_not_send_logout=True)
            self._cp.send_signal(SIGTERM) # send Ctrl+C
            sleep(2)
        else:
            self._uc.stop(do_not_send_logout=True)
        is_running = self._cp.poll()
        assert is_running is not None
        self._cp.terminate()

    def check_that_ufegw_process_killed(self):
        is_running = self._cp.poll()
        assert is_running is not None

    def logout_and_logon_as(self, user: str, passw: str) -> Optional[Dict[int, UFEGWService]]:
        uc = self.ufegw_client
        uc.logout()
        status, session_token = uc.logon(user=user, passw=passw)
        assert session_token is not None
        assert status == Message.Status(LOGIN_ACCEPTED)
        status, services = uc.service_list(force_refresh=True)
        assert status.status == UFE_OK
        assert services is not None
        _ufegw_env.session_token = session_token
        return services

    def logout_and_logon_as_user(self):
        ret = self.logout_and_logon_as("webuser", "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8")
        uc = _ufegw_env.ufegw_client
        user: UFEGWUser
        status, user = uc.check_logged_in_user_permission()
        assert status.status == UFE_OK
        assert user.logged_in == True
        assert user.login_id == "webuser"
        assert user.service_perms != -1
        self.current_user = user.login_id
        return ret

    def logout_and_logon_as_admin(self):
        ret = self.logout_and_logon_as("admin", "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8")
        uc = _ufegw_env.ufegw_client
        user: UFEGWUser
        status, user = uc.check_logged_in_user_permission()
        assert status.status == UFE_OK
        assert user.logged_in == True
        assert user.login_id == "admin"
        assert user.service_perms == -1
        self.current_user = user.login_id
        return ret

    def start_f8ptest(self, session_name: str):
        is_acceptor = "A" in session_name
        f8p = subprocess.Popen([f"{Env.FIX8PRO_ROOT}/f8ptest", "-sl" if is_acceptor else "-l", f"f8ptest_{session_name}.log", "-N", session_name, "-D", "-c", "f8ptest.xml"],
                                env={Env.OS_ENV_FIX8PRO_LICENSE_FILE: Env.UFEGW_LICENSE}, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        assert f8p.pid is not None
        assert f8p.returncode is None
        return f8p

# _local_env is a test environment that connects to itself w/o external UFEGW app
# set UFEedClient connection strings to point to each other
_ufegw_env: Optional[Env] = None


@pytest.fixture()
def ufegw_env_setup():
    # setup
    if Env.SKIP_UGEGW_TESTS:
        return
    # _ufegw_env is a test environment that connects external UFEGW app
    # requires running ufegw with proper config, see ufegw_1initiator_1acceptor
    global _ufegw_env
    if _ufegw_env is None:
        _ufegw_env = Env(conn_strs={
            SUBSCRIBER: f"tcp://127.0.0.1:{Env.CONFIG_MIDDLEWARE_PORT_PUBLISHER}",
            REQUESTER: f"tcp://127.0.0.1:{Env.CONFIG_MIDDLEWARE_PORT_RESPONDER}",
            RESPONDER: f"tcp://*:{Env.CONFIG_MIDDLEWARE_PORT_REQUESTER}"
        })
    assert _ufegw_env is not None
    try:
        _ufegw_env.connect()
        yield
    finally:
        # teardown
        _ufegw_env.disconnect()
        #del _ufegw_env


@pytest.fixture()
def ufegw_1initiator_1acceptor():
    # setup
    if Env.SKIP_UGEGW_TESTS:
        return
    global _ufegw_env
    # must be run after ufegw_env_setup
    assert _ufegw_env is not None
    assert _ufegw_env.ufegw_client.started
    f8pi_0: Optional[subprocess.Popen] = None
    f8pa_0: Optional[subprocess.Popen] = None
    try:
        f8pi_0 = _ufegw_env.start_f8ptest("SS8I")
        f8pa_0 = _ufegw_env.start_f8ptest("SS8A")
        sleep(2)
        yield
    finally:
        # teardown
        if f8pi_0 is not None:
            f8pi_0.send_signal(SIGTERM)
            f8pi_0.send_signal(SIGKILL)
        if f8pa_0 is not None:
            f8pa_0.send_signal(SIGTERM)
            f8pa_0.send_signal(SIGKILL)


@pytest.mark.usefixtures('ufegw_env_setup', scope='function')
@pytest.mark.timeout(20)
@pytest.mark.skipif(Env.SKIP_UGEGW_TESTS, reason=Env.TEST_SKIP_MESSAGE)
def test_ufegw_logout_logon_logout():
    uc = _ufegw_env.ufegw_client
    status = uc.logout()
    assert status.status == LOGOFF_SUCCESSFUL
    status, session_token = uc.logon(user="webuser", passw="pass")
    assert session_token is None
    assert status == Message.Status(INVALID_PASSWORD)
    status, session_token = uc.logon(user="webuser", passw="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8")
    assert session_token is not None
    assert status == Message.Status(LOGIN_ACCEPTED)
    status = uc.logout()
    assert status.status == LOGOFF_SUCCESSFUL


@pytest.mark.usefixtures('ufegw_env_setup', scope='function')
@pytest.mark.timeout(20)
@pytest.mark.skipif(Env.SKIP_UGEGW_TESTS, reason=Env.TEST_SKIP_MESSAGE)
def test_ufegw_wrong_request_params():
    uc: UFEedClient = _ufegw_env.ufegw_client.ufeed_client
    rep = uc.request(
            uc.create_message()
                .set_long_name("ABCDEF")
                .set_type(MsgType.st_system)
                .set_service_id(0)
                .set_sub_service_id(0)
                .add_field(UFE_CMD, 112233) # must be Message.Status(112233)
        )
    status = rep[UFE_RESPONSE_CODE]
    assert status != UFE_OK # wrong_request_params

    _ufegw_env.logout_and_logon_as_admin()
    rep = uc.request(
            uc.create_message()
                .set_long_name("ABCDEF")
                .set_type(MsgType.st_system)
                .set_service_id(0)
                .set_sub_service_id(0)
                .add_field(UFE_CMD, Message.Status(UFE_CMD_PUT_CONFIG))
                .add_field(UFE_CONFIG_NAME, "123")
                .add_field(UFE_CONFIG_RECORD, 123)
                .add_field(UFE_CONFIG_COMMIT_ACTION, UFE_CONFIG_COMMIT_ACTION) # must be Message.Status(UFE_CONFIG_COMMIT_ACTION)
        )
    status = rep[UFE_RESPONSE_CODE]
    assert status != UFE_OK # wrong_request_params


@pytest.mark.usefixtures('ufegw_env_setup', 'ufegw_1initiator_1acceptor', scope='function')
@pytest.mark.timeout(20)
@pytest.mark.skipif(Env.SKIP_UGEGW_TESTS, reason=Env.TEST_SKIP_MESSAGE)
def test_ufegw_service_list():
    uc = _ufegw_env.ufegw_client
    status, services = uc.service_list(force_refresh=True)
    assert status.status == UFE_OK
    assert len(services) == 2 # 1 initiator SS8I + 1 acceptor SS8A
    # check mandatory fields
    # todo: load config before testing service list
    for service_key, service in services.items():
        assert service.service_status is not None
        service_status = service.service_status
        assert service_status.service_version is not None
        assert service_status.service_id is not None
        assert service_status.sub_service_id is not None
        assert service_status.service_name is not None
        assert service_status.service_tag is not None
        assert service_status.service_status_string is not None
        assert service_status.service_uptime is not None
        assert service_status.service_fix_variant is not None
        assert service_status.service_fix_desc is not None
        assert service_status.service_sent is not None
        assert service_status.service_received is not None
        assert service_status.last_fix_recv_time is not None
        assert service_status.last_fix_send_time is not None
        assert service_status.session_flags is not None
        assert service_status.overrate is not None
        assert service_status.target_compid is not None
        assert service_status.sender_compid is not None

    s8a: UFEGWService
    s8a = uc.service(8, 1)
    assert s8a is not None
    assert s8a.service_status.service_id == 8
    assert s8a.service_status.service_name == "SS8A"

    s9i: UFEGWService
    s9i = uc.service(9, 0)
    assert s9i is not None
    assert s9i.service_status.service_id == 9
    assert s9i.service_status.service_name == "SS8I"

    # request stored service list
    status, services1 = uc.service_list()
    assert status.status == UFE_OK
    assert services1 is not None
    assert services1 == services

    # request service list again and update stored service list
    status, services2 = uc.service_list(force_refresh=True)
    assert status.status == UFE_OK
    assert services2 is not None
    assert len(services1) == len(services2)
    assert services1.keys() == services2.keys()

@pytest.mark.usefixtures('ufegw_env_setup', 'ufegw_1initiator_1acceptor', scope='function')
@pytest.mark.timeout(20)
@pytest.mark.skipif(Env.SKIP_UGEGW_TESTS, reason=Env.TEST_SKIP_MESSAGE)
def test_ufegw_service_dictionary():
    uc = _ufegw_env.ufegw_client
    services = _ufegw_env.logout_and_logon_as_user()
    assert services is not None
    assert len(services) >= 2

    # get initiator service
    service: UFEGWService
    for id, service in services.items():
        assert service is not None
        dic: UFEGWService.ServiceDictionary
        status, dic = service.dictionary()
        assert status.status == UFE_OK
        assert dic is not None
        assert len(dic.field_definitions) != 0
        assert len(dic.component_definitions) != 0
        assert len(dic.message_definitions) != 0
        # todo: add comparison to FIX XML dict here


def create_invalid_service() -> UFEGWService:
    uc = _ufegw_env.ufegw_client.ufeed_client
    service_record: Message.Builder = uc.create_message().add_field(UFE_SERVICE_ID, 99).add_field(UFE_SUBSERVICE_ID, 888).add_field(
        UFE_SERVICE_NAME, "invalid_service")
    invalid_service: UFEGWService = UFEGWService(service_record.build(), _ufegw_env.ufegw_client.ufeed_client, _ufegw_env.session_token)
    return invalid_service


@pytest.mark.usefixtures('ufegw_env_setup', 'ufegw_1initiator_1acceptor', scope='function')
@pytest.mark.timeout(20)
@pytest.mark.skipif(Env.SKIP_UGEGW_TESTS, reason=Env.TEST_SKIP_MESSAGE)
def test_ufegw_service_status_start_stop_restart():
    uc = _ufegw_env.ufegw_client
    services = _ufegw_env.logout_and_logon_as_user()
    assert services is not None
    assert len(services) >= 2

    # get first initiator
    service: UFEGWService = uc.service(9, 0)
    service_status: UFEGWService.Status
    status, service_status = service.status(force_refresh=True)
    assert status.status == ACCESS_DENIED
    assert service_status is None

    # logout/logon with admin
    services = _ufegw_env.logout_and_logon_as_admin()
    service = uc.service(9, 0)
    sleep(2)
    status, service_status = service.status(force_refresh=True)
    assert status.status == UFE_OK
    assert service_status is not None
    if service_status.service_status_string == "session_terminated":
        status = service.start()
        assert status.status == UFE_OK
        sleep(2)
        status, service_status = service.status(force_refresh=True)
        assert status.status == UFE_OK
    assert service_status.service_status_string == "continuous"

    # start/stop of invalid service
    invalid_service: UFEGWService = create_invalid_service()
    status = invalid_service.stop()
    assert status.status == UNKNOWN_SERVICE
    status = invalid_service.start()
    assert status.status == UNKNOWN_SERVICE

    # start/stop/restart of initiator
    status = service.stop()
    assert status.status == UFE_OK
    sleep(2)
    status, service_status = service.status(force_refresh=True)
    assert status.status == UFE_OK
    assert service_status.service_status_string != "continuous"
    status = service.start()
    assert status.status == UFE_OK
    sleep(2)
    status = service.start()
    assert status.status == SERVICE_ALREADY_ESTABLISHED
    status, service_status = service.status(force_refresh=True)
    assert status.status == UFE_OK
    assert service_status.service_status_string == "continuous"
    status = service.restart()
    assert status.status == UFE_OK
    sleep(2)
    status, service_status = service.status(force_refresh=True)
    assert service_status.service_status_string == "continuous"
    status = service.start()
    assert status.status == SERVICE_ALREADY_ESTABLISHED
    sleep(2)
    status, service_status = service.status(force_refresh=True)
    assert service_status.service_status_string == "continuous"

    # @todo: start/stop of acceptor
    ...


@pytest.mark.usefixtures('ufegw_env_setup', 'ufegw_1initiator_1acceptor', scope='function')
@pytest.mark.timeout(20)
@pytest.mark.skipif(Env.SKIP_UGEGW_TESTS, reason=Env.TEST_SKIP_MESSAGE)
def test_ufegw_service_session_cache_send_recv():
    uc = _ufegw_env.ufegw_client
    services = _ufegw_env.logout_and_logon_as_admin()
    # get acceptor service
    service: UFEGWService = uc.service(9, 0)

    # add app level messages by sending NOS - does not work, need a drop copy config
    # fix50sp2 = FIX50SP2_Fields
    # rep = uc.ufeed_client.request(
    #     uc.ufeed_client.create_message()
    #         .set_long_name("NOS")
    #         .set_type(MsgType.st_fixmsg)
    #         .set_service_id(9)
    #         .set_sub_service_id(0)
    #         .add_field(fix50sp2.MsgType.tag, fix50sp2.MsgType.NEWORDERSINGLE, Location.fl_header)
    #         .add_field(fix50sp2.Symbol.tag, "AAABBB")
    #         .add_field(fix50sp2.ClOrdID.tag, "cl123456")
    #         .add_field(fix50sp2.OrderQty.tag, 11, precision=2)
    #         .add_field(fix50sp2.Price.tag, 987.654, precision=2)
    #         .add_field(fix50sp2.OrdType.tag, fix50sp2.OrdType.LIMIT)
    #         .add_field(fix50sp2.Side.tag, fix50sp2.Side.BUY)
    #         .add_field(fix50sp2.TimeInForce.tag, fix50sp2.TimeInForce.GOOD_TILL_CANCEL)
    #         .add_field(fix50sp2.TransactTime.tag, datetime.now())
    # )
    # assert rep[UFE_RESPONSE_CODE].status == UFE_OK
    # sleep(3)    # wait for ER

    # resend test
    status, resent_in = service.session_cache(direction=UFEGWService.SessionCacheDirection.INBOUND, begin_seqnum=0)
    assert status.status == INVALID_SEQUENCE
    status, resent_in = service.session_cache(direction=3)
    assert status.status == INVALID_DIRECTION
    status, resent_in = service.session_cache(direction=UFEGWService.SessionCacheDirection.INBOUND)
    assert status.status == UFE_OK
    assert resent_in is not None
    status, resent_out = service.session_cache(direction=UFEGWService.SessionCacheDirection.OUTBOUND)
    assert status.status == UFE_OK
    assert resent_out is not None

    send_recv: UFEGWService.SendRecv
    status, send_recv = service.send_recv()
    assert status.status == UFE_OK
    assert send_recv.send_seqnum is not None
    assert send_recv.recv_seqnum is not None


@pytest.mark.usefixtures('ufegw_env_setup', scope='function')
@pytest.mark.timeout(20)
@pytest.mark.skipif(Env.SKIP_UGEGW_TESTS, reason=Env.TEST_SKIP_MESSAGE)
def test_ufegw_users():
    uc = _ufegw_env.ufegw_client
    services = _ufegw_env.logout_and_logon_as_user()
    # get users
    user_list: UFEGWUserList
    status, user_list = uc.user_list(force_refresh=True)
    assert status.status == ACCESS_DENIED

    services = _ufegw_env.logout_and_logon_as_admin()
    status, user_list = uc.user_list(force_refresh=True)
    assert status.status == UFE_OK
    assert user_list is not None
    assert user_list.count == 2
    user_ids = user_list.ids
    assert user_ids[0] == "admin"
    assert user_ids[1] == "webuser"

    status = user_list.remove("xyz")
    assert status.status == USER_DEL_FAILURE or status.status == UFE_OK

    status = user_list.add("xyz", "123", 0, False)
    assert status.status == UFE_OK
    status, user_list = uc.user_list(force_refresh=True)
    assert status.status == UFE_OK
    assert user_list["xyz"] is not None
    assert user_list["xyz"].logged_in == False
    assert user_list["xyz"].view_only == False
    assert user_list["xyz"].service_perms == 0

    status = user_list.add("xyz", "456", 1, True)
    assert status.status == UFE_OK
    status, user_list = uc.user_list(force_refresh=True)
    assert status.status == UFE_OK
    assert user_list["xyz"] is not None
    assert user_list["xyz"].logged_in == False
    assert user_list["xyz"].view_only == True
    assert user_list["xyz"].service_perms == 1

    status = user_list.update("xyz", "789", 2, True)
    assert status.status == UFE_OK
    status, user_list = uc.user_list(force_refresh=True)
    assert status.status == UFE_OK
    assert user_list["xyz"] is not None
    assert user_list["xyz"].logged_in == False
    assert user_list["xyz"].view_only == True
    assert user_list["xyz"].service_perms == 2

    status = user_list.remove("xyz")
    assert status.status == UFE_OK
    status, user_list = uc.user_list(force_refresh=True)
    assert status.status == UFE_OK
    assert user_list["xyz"] is None


@pytest.mark.usefixtures('ufegw_env_setup', scope='function')
@pytest.mark.timeout(20)
@pytest.mark.skipif(Env.SKIP_UGEGW_TESTS, reason=Env.TEST_SKIP_MESSAGE)
def test_ufegw_configs():
    uc = _ufegw_env.ufegw_client
    services = _ufegw_env.logout_and_logon_as_user()
    # get configs
    conf_list: UFEGWConfigList
    status, conf_list = uc.config_list(force_refresh=True)
    assert status.status == ACCESS_DENIED

    # list
    services = _ufegw_env.logout_and_logon_as_admin()
    status, conf_list = uc.config_list(force_refresh=True)
    assert status.status == UFE_OK
    assert conf_list is not None
    assert len(conf_list.config_list) == 3

    # get
    conf = conf_list[UFE_CONFIG_MAINCFG_TAG]
    conf_rec = conf.record
    assert conf is not None
    status, conf1 = conf_list.get(conf)
    assert status.status == UFE_OK
    assert conf1.record == conf_rec
    status, conf2 = conf_list.get(UFEGWConfig(name="abc"))
    assert status.status == CONFIG_FILE_ERROR
    status, conf2 = conf_list.get(UFEGWConfig(id=123))
    assert status.status == UFE_OK  # todo, fixme: should be here some sort of error since 123 config does not exist

    # put
    conf = conf_list[UFE_CONFIG_MAINCFG_TAG]
    conf_rec = conf.record
    assert conf is not None
    status, conf1 = conf_list.put(conf, UFEGWConfigList.CommitAction.REPLACE_ONLY)
    assert status.status == UFE_OK
    assert conf1.record == conf_rec

    new_name = f"{conf1.name}/abc"
    new_conf: UFEGWConfig = UFEGWConfig(name=new_name, rec="<!-- test rec -->")
    status, conf2 = conf_list.remove(new_conf)
    assert status.status == UNKNOWN_CONFIG or status.status == UFE_OK
    status, conf2 = conf_list.put(new_conf, UFEGWConfigList.CommitAction.REPLACE_ONLY)
    assert status.status == UFE_OK  # should be error here since config does not exists
    status, conf3 = conf_list.put(new_conf, UFEGWConfigList.CommitAction.COMMIT_NEW)
    assert status.status == UFE_OK
    status, conf4 = conf_list.put(new_conf, UFEGWConfigList.CommitAction.COMMIT_NEW)
    assert status.status == UFE_OK
    status, conf4 = conf_list.put(new_conf, UFEGWConfigList.CommitAction.REPLACE_ONLY)
    assert status.status == UFE_OK
    status, conf2 = conf_list.remove(new_conf)
    assert status.status == UFE_OK

    # reload
    ini_name = f"{conf1.name}/SS9I"
    ini_conf: UFEGWConfig = UFEGWConfig(
        name=ini_name, rec="""
        <fix8>
            <session name="SS9I" role="initiator" sender_comp_id="YYI9_XXA9" target_comp_id="XXA9_YYI9" port="11099" active="true" persist="file0"/>
            <ufegw>
                <profiles>
                    <profile name="SS9I" role="initiator" ns="FIX50SP2" serviceid="29" servicetag="ss9i-29" giveupreset="10" >
                        <authenticate rejectonerror="false"/>
                    </profile>
                </profiles>
            </ufegw>
        </fix8>""")
    acc_name = f"{conf1.name}/SS9A"
    acc_conf: UFEGWConfig = UFEGWConfig(
        name=acc_name, rec="""
        <fix8>
            <session name="SS9A" role="acceptor" sender_comp_id="YYA9_XXI9"  target_comp_id="XXI9_YYA9" port="11019" active="true" persist="file0"/>
            <ufegw>
                <profiles>
                    <profile name="SS9A" role="acceptor" ns="FIX50SP2" serviceid="19" servicetag="ss9a-19" giveupreset="10" >
                        <authenticate rejectonerror="false"/>
                    </profile>
                </profiles>
            </ufegw>
        </fix8>""")
    status, conf = conf_list.remove(ini_conf)
    assert status.status == UFE_OK or status.status == UNKNOWN_CONFIG
    status, conf = conf_list.remove(acc_conf)
    assert status.status == UFE_OK or status.status == UNKNOWN_CONFIG

    status, conf_ini = conf_list.put(ini_conf, UFEGWConfigList.CommitAction.REPLACE_ONLY)
    assert status.status == UFE_OK
    status, conf_acc = conf_list.put(acc_conf, UFEGWConfigList.CommitAction.REPLACE_ONLY)
    assert status.status == UFE_OK

    status, conf = conf_list.get(conf_ini)
    assert status.status == UFE_OK
    assert conf.record == ini_conf.record

    status, conf = conf_list.get(conf_acc)
    assert status.status == UFE_OK
    assert conf.record == acc_conf.record

    # start 1 initiator and 1 acceptor
    f8pi_0: Optional[subprocess.Popen] = None
    f8pa_0: Optional[subprocess.Popen] = None
    try:
        status = conf_list.load_profile(conf_acc)
        assert status.status == UFE_OK
        f8pi_0 = _ufegw_env.start_f8ptest("SS9I")
        f8pa_0 = _ufegw_env.start_f8ptest("SS9A")
        sleep(2)
        status = conf_list.load_profile(conf_ini)
        assert status.status == UFE_OK
        # wait for connection complete
        sleep(2)
        status, services = uc.service_list(force_refresh=True)
        assert status.status == UFE_OK
        ini_svc = uc.service(29, 0)
        assert ini_svc is not None
        assert ini_svc.service_status.service_status_string == "continuous"
        sleep(2)
        acc_svc = uc.service(19, 1)
        assert acc_svc is not None
        assert acc_svc.service_status.service_status_string == "continuous" or acc_svc.service_status.service_status_string == "logon_received"

    finally:
        # kill ini/acc
        if f8pi_0 is not None:
            f8pi_0.send_signal(SIGTERM)
            f8pi_0.send_signal(SIGKILL)
        if f8pa_0 is not None:
            f8pa_0.send_signal(SIGTERM)
            f8pa_0.send_signal(SIGKILL)

    # sleep(2)
    # status, services = uc.service_list(force_refresh=True)
    # assert status.status == UFE_OK
    # ini_svc = uc.service(29, 0)
    # assert ini_svc is None
    # acc_svc = uc.service(19, 1)
    # assert acc_svc is None

    status, conf = conf_list.remove(ini_conf)
    assert status.status == UFE_OK
    status, conf = conf_list.remove(acc_conf)
    assert status.status == UFE_OK
    ...


@pytest.mark.usefixtures('ufegw_env_setup', scope='function')
@pytest.mark.timeout(20)
@pytest.mark.skipif(Env.SKIP_UGEGW_TESTS, reason=Env.TEST_SKIP_MESSAGE)
def test_ufegw_system_status_strings():
    uc = _ufegw_env.ufegw_client
    system_status: UFEGWClient.SystemStatus
    status, system_status = uc.system_status()
    assert status.status == UFE_OK
    assert system_status is not None
    assert system_status.active_sessions is not None
    assert system_status.uptime is not None
    assert system_status.workers != 0

    status, system_strings = uc.system_strings()
    assert status.status == UFE_OK
    assert system_strings is not None
    assert len(system_strings) != 0


@pytest.mark.usefixtures('ufegw_env_setup', scope='function')
@pytest.mark.timeout(20)
@pytest.mark.skipif(True or Env.SKIP_UGEGW_TESTS, reason=Env.TEST_SKIP_MESSAGE) # skipped until RPC transformation is ready
def test_ufegw_transform_rpc():
    uc = _ufegw_env.ufegw_client

    def rep_handler(msg: Message):
        return msg

    uc.add_rep_handler(rep_handler)
    f8pi_0: Optional[subprocess.Popen] = None
    f8pa_0: Optional[subprocess.Popen] = None

    try:
        # test transform rpc here...
        _ufegw_env.logout_and_logon_as_admin()
        status, conf_list = uc.config_list(force_refresh=True)
        assert status.status == UFE_OK
        assert conf_list is not None
        conf = conf_list[UFE_CONFIG_MAINCFG_TAG]
        conf_rec = conf.record
        assert conf is not None
        status, conf1 = conf_list.get(conf)
        assert status.status == UFE_OK
        assert conf1.record == conf_rec

        acc_name = f"{conf1.name}/SS9A"
        acc_conf: UFEGWConfig = UFEGWConfig(
            name=acc_name, rec=f"""
            <fix8>
                <session name="SS9A" role="acceptor" sender_comp_id="YYA9_XXI9"  target_comp_id="XXI9_YYA9" port="11019" active="true" persist="file0"/>
                <!--session name="SS9I" role="initiator" sender_comp_id="YYI9_XXA9" target_comp_id="XXA9_YYI9" port="11099" active="true" persist="file0"/-->
                <ufegw>
                    <profiles>
                        <profile name="SS9A" role="acceptor" ns="FIX50SP2" serviceid="19" servicetag="ss9a-19" giveupreset="10" >
                            <authenticate rejectonerror="false"/>
                            {Env.CONFIG_TRANSFORM_RPC_ALL}
                        </profile>
                        <!--profile name="SS9I" role="initiator" ns="FIX50SP2" serviceid="29" servicetag="ss9i-29" giveupreset="10" >
                            <authenticate rejectonerror="false"/>
                            {Env.CONFIG_TRANSFORM_RPC_ALL}
                        </profile-->
                    </profiles>
                </ufegw>
            </fix8>""")
        status, conf = conf_list.remove(acc_conf)
        assert status.status == UFE_OK or status.status == UNKNOWN_CONFIG
        status, conf_acc = conf_list.put(acc_conf, UFEGWConfigList.CommitAction.COMMIT_REPLACE_AND_LOAD)
        assert status.status == UFE_OK
        sleep(2)

        status = conf_list.load_profile(conf_acc)
        assert status.status == UFE_OK
        f8pi_0 = _ufegw_env.start_f8ptest("SS9I")
        # f8pa_0 = _ufegw_env.start_f8ptest("SS9A")
        sleep(2)
        status, services = uc.service_list(force_refresh=True)
        assert status.status == UFE_OK
        # ini_svc = uc.service(29, 0)
        # assert ini_svc is not None
        # assert ini_svc.service_status.service_status_string == "continuous"
        sleep(2)
        acc_svc = uc.service(19, 1)
        assert acc_svc is not None
        assert acc_svc.service_status.service_status_string == "continuous" or acc_svc.service_status.service_status_string == "logon_received"

        # get acceptor service
        service: UFEGWService = uc.service(19, 1)
        # add app level messages by sending NOS - does not work
        fix50sp2 = FIX50SP2_Fields
        rep = uc.ufeed_client.request(
            uc.ufeed_client.create_message()
                .set_long_name("NOS")
                .set_type(MsgType.st_fixmsg)
                .set_service_id(9)
                .set_sub_service_id(0)
                .add_field(fix50sp2.MsgType.tag, fix50sp2.MsgType.NEWORDERSINGLE, Location.fl_header)
                .add_field(fix50sp2.Symbol.tag, "AAABBB")
                .add_field(fix50sp2.ClOrdID.tag, "cl123456")
                .add_field(fix50sp2.OrderQty.tag, 11, precision=2)
                .add_field(fix50sp2.Price.tag, 987.654, precision=2)
                .add_field(fix50sp2.OrdType.tag, fix50sp2.OrdType.LIMIT)
                .add_field(fix50sp2.Side.tag, fix50sp2.Side.BUY)
                .add_field(fix50sp2.TimeInForce.tag, fix50sp2.TimeInForce.GOOD_TILL_CANCEL)
                .add_field(fix50sp2.TransactTime.tag, datetime.now())
        )
        assert rep[UFE_RESPONSE_CODE].status == UFE_OK
        sleep(3)    # wait for ER

    finally:
        # kill ini/acc
        if f8pi_0 is not None:
            f8pi_0.send_signal(SIGTERM)
            f8pi_0.send_signal(SIGKILL)
        if f8pa_0 is not None:
            f8pa_0.send_signal(SIGTERM)
            f8pa_0.send_signal(SIGKILL)
        uc.remove_rep_handler(rep_handler)

@pytest.mark.usefixtures('ufegw_env_setup', scope='function')
@pytest.mark.timeout(20)
@pytest.mark.skipif(Env.SKIP_UGEGW_TESTS, reason=Env.TEST_SKIP_MESSAGE)
def test_ufegw_transform_plugins():
    uc = _ufegw_env.ufegw_client
    # test transform plugins here...


@pytest.mark.usefixtures('ufegw_env_setup', scope='function')
@pytest.mark.timeout(20)
@pytest.mark.skipif(Env.SKIP_UGEGW_TESTS, reason=Env.TEST_SKIP_MESSAGE)
def test_ufegw_subscribe():
    uc = _ufegw_env.ufegw_client
    # test subscribe here...


# MUST be the last test in test suite
@pytest.mark.usefixtures('ufegw_env_setup', scope='function')
@pytest.mark.timeout(20)
@pytest.mark.skipif(Env.SKIP_UGEGW_TESTS, reason=Env.TEST_SKIP_MESSAGE)
def test_ufegw_shutdown_kill():
    uc = _ufegw_env.ufegw_client
    services = _ufegw_env.logout_and_logon_as_user()
    status = uc.shutdown()
    assert status.status == ACCESS_DENIED

    services = _ufegw_env.logout_and_logon_as_admin()
    status = uc.shutdown()
    assert status.status == LOGOFF_SUCCESSFUL

    _ufegw_env.stop_ufegw_process()
    _ufegw_env.start_ufegw_process()
    sleep(2)
    _ufegw_env.connect()

    #todo: fixme: kill doesn't work since we have no reply from UFEGW (killed) - middleware request hangs and does not return
    #kill requires to be logged in!
    #services = _ufegw_env.logout_and_logon_as_admin()
    #status = uc.kill()
    #assert status.status == UFE_OK
    _ufegw_env.stop_ufegw_process()
    _ufegw_env.check_that_ufegw_process_killed()
