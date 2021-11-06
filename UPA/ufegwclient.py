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
from typing import Optional, List, Dict
from uuid import UUID

from UPA import *


class UFEGWService:
    """
    UFEGW Service class: represents an UFEGW service.
    Handles most of service calls and contains service state from last update
    """
    class Status:
        """Service status class. Holds all service properties extracted from UFEed message"""
        def __init__(self, msg: Message):
            """Initializes UFEGW service status members
            :arg msg UFEed message to populate status properties"""
            self.service_status: int = msg[UFE_SERVICE_STATUS]
            self.service_version: int = msg[UFE_SERVICE_VERSION]
            self.service_id: int = msg[UFE_SERVICE_ID]
            self.sub_service_id: int = msg[UFE_SUBSERVICE_ID]
            self.service_name: str = msg[UFE_SERVICE_NAME]
            self.service_tag: str = msg[UFE_SERVICE_TAG]
            self.service_status_string: str = msg[UFE_SERVICE_STATUS_STRING]
            self.service_uptime: int = msg[UFE_SERVICE_UPTIME]
            self.service_fix_variant: str = msg[UFE_SERVICE_FIX_VARIANT]
            self.service_fix_desc: str = msg[UFE_SERVICE_FIX_DESC]
            self.service_sent: int = msg[UFE_SERVICE_SENT]
            self.service_received: int = msg[UFE_SERVICE_RECEIVED]
            self.service_bytes_sent: Optional[int] = msg[UFE_SERVICE_BYTES_SENT]
            self.service_bytes_received: Optional[int] = msg[UFE_SERVICE_BYTES_RECEIVED]
            self.last_fix_recv_time: datetime = msg[UFE_LAST_FIX_RECV_TIME]
            self.last_fix_send_time: datetime = msg[UFE_LAST_FIX_SEND_TIME]
            self.connect_attempts: Optional[int] = msg[UFE_CONNECT_ATTEMPTS]
            self.is_acceptor: Optional[bool] = msg[UFE_IS_ACCEPTOR]
            self.next_fix_send_seq: Optional[int] = msg[UFE_NEXT_FIX_SEND_SEQ]
            self.next_fix_recv_seq: Optional[int] = msg[UFE_NEXT_FIX_RECV_SEQ]
            self.session_flags: int = msg[UFE_SESSION_FLAGS]
            self.overrate: int = msg[UFE_OVERRATE]
            self.target_compid: str = msg[COMMON_TARGETCOMPID]
            self.sender_compid: str = msg[COMMON_SENDERCOMPID]

    def __init__(self, msg: Message, uc: UFEedClient, session_token: UUID):
        """Initializes UFEGW service class
        :arg msg UFEed message to populate service status from
        :arg uc UFEedClient object to perform requests to
        :arg session_token recent session token to set to UFEedClient requests"""
        self.service_status: UFEGWService.Status = UFEGWService.Status(msg)
        # private members
        self._uc: UFEedClient = uc
        self._session_token: UUID = session_token

    @property
    def service_id(self) -> int:
        """Property that gets service ID
        :returns service id"""
        return self.service_status.service_id

    @property
    def sub_service_id(self) -> int:
        """Property that gets subservice ID
        :returns subservice id"""
        return self.service_status.sub_service_id

    def _request(self, cmd: int, long_name: str = None, tr: Callable[[Message.Builder], Message.Builder] = lambda m: m) -> (Message.Status, Message):
        if self._session_token is None:
            return Message.Status(NOT_LOGGED_IN), None
        rep = self._uc.request(tr(
            self._uc.create_message()
                .set_long_name(long_name)
                .set_type(MsgType.st_system)
                .set_service_id(self.service_id)
                .set_sub_service_id(self.sub_service_id)
                .add_field(UFE_CMD, Message.Status(cmd))
        ))
        return rep[UFE_RESPONSE_CODE], rep

    def status(self, force_refresh: bool = False) -> (Message.Status, Optional[Status]):
        """Gets or requests service status
        :arg force_refresh request service status from UFEGW if True, otherwise returns cached value
        :returns a pair of UFEGW request status and service status"""
        if self.status is not None and not force_refresh:
            return Message.Status(UFE_OK), self.status
        status, rep = self._request(UFE_CMD_SERVICE_STATUS, "status request")
        if status.status != UFE_OK:
            return status, None
        self.service_status = UFEGWService.Status(rep)
        return status, self.service_status

    def start(self) -> Message.Status:
        """Starts service
        :returns service start request status"""
        status, rep = self._request(UFE_CMD_SERVICE_START, "service start")
        return status

    def stop(self) -> Message.Status:
        """Stops service
        :returns service stop request status"""
        status, rep = self._request(UFE_CMD_SERVICE_STOP, "service stop")
        return status

    def restart(self):
        """Restarts service
        :returns service restart request status"""
        status, rep = self._request(UFE_CMD_SERVICE_RESTART, "service restart")
        return status

    class FieldDef:
        """Field definition for UFEGW service dictionary"""
        def __init__(self, msg: Message):
            assert msg.name == "field_definition"
            self.tag: int = msg[UFE_FIX8_TAG]
            self.tag_string: str = msg[UFE_FIX8_TAG_STRING]
            self.type_string: Optional[str] = msg[UFE_FIX8_TYPE_STRING]
            self.underlying_type_string: Optional[str] = msg[UFE_FIX8_UNDERLYING_TYPE_STRING]
            self.tag_type: Optional[int] = msg[UFE_FIX8_TAG_TYPE]  # see FieldType
            self.realms: Optional[Dict[Union[int, str], str]] = None
            realms: List["Message"] = msg[UFE_FIELD_REALM_RECORDS]
            if realms is not None:
                self.realms = {}
                for realm in realms:
                    self.realms[realm[UFE_FIELD_REALM_VALUE]] = realm[UFE_FIELD_REALM_DESCRIPTION]

    class ComponentDef:
        """Component definition for UFEGW service dictionary"""
        def __init__(self, msg: Message):
            assert msg.name == "component_definition"
            self.component_string: str = msg[UFE_FIX8_COMPONENT_STRING]
            self.component: int = msg[UFE_FIX8_COMPONENT]  # component index

    class MessageFieldDef:
        """MessageField definition for UFEGW service dictionary"""
        def __init__(self, msg: Message):
            self.tag: int = msg[UFE_FIX8_TAG]
            self.flag: int = msg[UFE_FIX8_FLAG]
            self.component: Optional[int] = msg[UFE_FIX8_COMPONENT]
            self.nested: Optional[Dict[str, "UFEGWService.MessageFieldDef"]] = None
            nested = msg[UFE_FIELD_DEFINITION_RECORDS]
            if nested is not None:
                self.nested = {}
                for nest in nested:
                    self.nested[nest[UFE_FIX8_TAG]] = UFEGWService.MessageFieldDef(nest)

    class MessageDef:
        """Message definition for UFEGW service dictionary"""
        def __init__(self, msg: Message):
            assert msg.name == "message_definition"
            self.tag: str = msg[UFE_FIX8_TAG]
            self.tag_string: str = msg[UFE_FIX8_TAG_STRING]
            self.message_definition_records: Dict[int, UFEGWService.MessageFieldDef] = {}
            fld: Message
            for fld in msg[UFE_MESSAGE_DEFINITION_RECORDS]:
                self.message_definition_records[fld[UFE_FIX8_TAG]] = UFEGWService.MessageFieldDef(fld)

    class ServiceDictionary:
        """Service dictionary that resulted as a response for UFEGW dictionary request"""
        def __init__(self, msg: Message):
            """Creates service dictionary
            :arg msg UFEGW message to initialize members from"""
            self.service_fix_variant: str = msg[UFE_SERVICE_FIX_VARIANT]
            self.service_fix_desc: str = msg[UFE_SERVICE_FIX_DESC]
            self.service_version: int = msg[UFE_SERVICE_VERSION]
            # contains 2 or 3 rpt grps: 1st - field definitions, 2nd - componnet definitions, 3rd - message definitions
            self.field_definitions: Dict[int, UFEGWService.FieldDef] = {}
            self.component_definitions: Dict[int, UFEGWService.ComponentDef] = {}
            self.message_definitions: Dict[int, UFEGWService.MessageDef] = {}
            groups = msg[UFE_FIELD_DEFINITION_RECORDS]
            assert len(groups) == 2 or len(groups) == 3
            definition: Message
            i = 0
            for definition in groups[i][UFE_FIELD_DEFINITION_RECORDS]:
                self.field_definitions[definition[UFE_FIX8_TAG]] = UFEGWService.FieldDef(definition)
            i += 1
            if len(groups) == 3:
                for definition in groups[i][UFE_COMPONENT_DEFINITION_RECORDS]:
                    self.component_definitions[definition[UFE_FIX8_COMPONENT]] = UFEGWService.ComponentDef(definition)
                i += 1
            for definition in groups[i][UFE_MESSAGE_DEFINITION_RECORDS]:
                self.message_definitions[definition[UFE_FIX8_TAG]] = UFEGWService.MessageDef(definition)

    def dictionary(self) -> (Message.Status, Optional[ServiceDictionary]):
        """Requests service dictionary
        :returns a pair of UFEGW status request and service dictionary"""
        status, rep = self._request(UFE_CMD_DICTIONARY, "dictionary request")
        if status.status != UFE_OK:
            return status, None
        dic: UFEGWService.ServiceDictionary = UFEGWService.ServiceDictionary(rep)
        return status, dic

    class SessionCacheDirection:
        """Enum for UFEGW session cache request direction"""
        INBOUND = 1
        OUTBOUND = 2

    def session_cache(self, direction: int, begin_seqnum: int = 1, end_seqnum: int = 0, filter: str = "") -> (Message.Status, Optional[int]):
        """Requests service session cache
        :arg direction a value from SessionCacheDirection to define cache direction to request
        :arg begin_seqnum begin sequence number
        :arg end_seqnum end sequence number
        :arg filter filter to filter out result messages
        :returns a pair of UFEGW request status and cached messages"""
        status, rep = self._request(UFE_CMD_SESSION_CACHE, "session cache request",
                                    tr=lambda m:
                                    m.add_field(UFE_CACHE_DIRECTION, direction)
                                    .add_field(UFE_CACHE_SEQUENCE_BEGIN, begin_seqnum)
                                    .add_field(UFE_CACHE_SEQUENCE_END, end_seqnum)
                                    .add_field(UFE_LOG_FILTER, filter)
                                    )
        if status.status != UFE_OK:
            return status, None
        return status, rep[UFE_CACHE_MESSAGES]

    class SendRecv:
        """Sender and receiver seqnunce numbers"""
        def __init__(self, send_seqnum: Optional[int], recv_seqnum: Optional[int]):
            self.send_seqnum: Optional[int] = send_seqnum
            self.recv_seqnum: Optional[int] = recv_seqnum

    def send_recv(self) -> (Message.Status, Optional[SendRecv]):
        """Requests service last sender/receiver sequence numbers
        :returns a pair of UFEGW request status and SendRecv object with recent sender/receiver sequence numbers"""
        status, rep = self._request(UFE_CMD_GET_SEND_RECV, "last_send_recv_seqnums request")
        if status.status != UFE_OK:
            return status, None
        return status, UFEGWService.SendRecv(send_seqnum=rep[UFE_NEXT_FIX_SEND_SEQ], recv_seqnum=rep[UFE_NEXT_FIX_RECV_SEQ])

    def session_flags(self):
        """Not implemented"""
        ...

    def set_session_flags(self):
        """Not implemented"""
        ...


class UFEGWUser:
    """UFEGW user class
    :arg msg UFEGW message to initialize members from"""
    def __init__(self, msg: Message):
        self.login_id: str = msg[UFE_LOGIN_ID]
        self.service_perms: int = msg[UFE_USER_SERVICE_PERMS]
        self.logged_in: bool = msg[UFE_LOGGED_IN]
        self.view_only: bool = msg[UFE_USER_VIEWONLY]


class UFEGWUserList():
    """UFEGW user list class
    :arg msg UFEGW message to initialize members from
    :arg uc UFEedClient object to perform requests to
    :arg session_token recent session token"""
    def __init__(self, msg: Message, uc: UFEedClient, session_token: UUID):
        self._uc = uc
        self._session_token: UUID = session_token
        self._user_list: Dict[str, UFEGWUser] = {}
        for u in msg[UFE_USER_RECORDS]:
            self._user_list[u[UFE_LOGIN_ID]] = UFEGWUser(u)

    @property
    def user_list(self):
        """Property that gets cached user list
        :returns cached user list"""
        return self._user_list

    @property
    def count(self):
        """Property that gets length of cached user list
        :returns length of cached user list"""
        return len(self._user_list)

    @property
    def ids(self):
        """Property that gets cached user IDs
        :returns cached user IDs"""
        return sorted(self._user_list.keys())

    def __getitem__(self, login_id: str):
        """Indexer that gets user by ID
        :arg login_id user ID to find
        :returns user with given ID or None if not found"""
        return self._user_list.get(login_id, None)

    def _request(self, cmd: int, long_name: str = None, tr: Callable[[Message.Builder], Message.Builder] = lambda m: m) -> (Message.Status, Message):
        if self._session_token is None:
            return Message.Status(NOT_LOGGED_IN), None
        rep = self._uc.request(tr(
            self._uc.create_message()
                .set_long_name(long_name)
                .set_type(MsgType.st_system)
                .add_field(UFE_CMD, Message.Status(cmd))
        ))
        return rep[UFE_RESPONSE_CODE], rep

    def add(self, login_id: str, login_pw: str, service_perms: int, view_only: bool) -> Message.Status:
        """Adds user to UFEGW user list. User list must be request again after addition.
        :arg login_id user ID
        :arg login_pw hashed user password
        :arg service_perms services access permissions
        :arg view_only True for view only user
        :returns UFEGW request status"""
        status, rep = self._request(UFE_CMD_ADD_USER, "add user",
                                    tr=lambda m:
                                    m.add_field(UFE_LOGIN_ID, login_id)
                                    .add_field(UFE_LOGIN_PW, login_pw)
                                    .add_field(UFE_USER_SERVICE_PERMS, service_perms)
                                    .add_field(UFE_USER_VIEWONLY, view_only))
        return status

    def update(self, login_id: str, login_pw: str, service_perms: int, view_only: bool) -> Message.Status:
        """Update user at UFEGW user list. User list must be request again after the update.
        :arg login_id user ID
        :arg login_pw hashed user password
        :arg service_perms services access permissions
        :arg view_only True for view only user
        :returns UFEGW request status"""
        status, rep = self._request(UFE_CMD_UPDATE_USER, "update user",
                                    tr=lambda m:
                                    m.add_field(UFE_LOGIN_ID, login_id)
                                    .add_field(UFE_LOGIN_PW, login_pw)
                                    .add_field(UFE_USER_SERVICE_PERMS, service_perms)
                                    .add_field(UFE_USER_VIEWONLY, view_only))
        return status

    def remove(self, login_id: str) -> Message.Status:
        """Removes user from UFEGW user list. User list must be request again after the deletion.
        :arg login_id user ID
        :returns UFEGW request status"""
        status, rep = self._request(UFE_CMD_REMOVE_USER, "remove user", tr=lambda m: m.add_field(UFE_LOGIN_ID, login_id))
        return status


class UFEGWConfig:
    """UFEGW configuration class"""
    def __init__(self, msg: Message = None, id: Optional[int] = None, name: Optional[str] = None, rec: Optional[str] = None):
        """Creates UFEGW configuration from either msg or config properties
        :arg msg UFEGW message to initialize from if not None
        :arg id config id to use if msg is None
        :arg name config name to use if msg is None
        :arg rec config to use if msg is None"""
        if msg is None:
            self.id: Optional[int] = id
            self.name: Optional[str] = name
            self.record: Optional[str] = rec
        else:
            self.id: Optional[int] = msg[UFE_CONFIG_ID]
            self.name: str = msg[UFE_CONFIG_NAME]
            self.description: str = msg[UFE_CONFIG_DESCRIPTION]
            self.record: Optional[str] = rec


class UFEGWConfigList:
    """UFEGW configuration list"""
    def __init__(self, msg: Message, uc: UFEedClient, session_token: UUID):
        """Creates UFEGW configuration list
        :arg msg UFEGW message to initialize from
        :arg uc UFEedClient object to send requests to
        :arg session_token recent session token"""
        self._uc = uc
        self._session_token: UUID = session_token
        self._conf_list: Dict[int, UFEGWConfig] = {}
        for u in msg[UFE_CONFIG_RECORDS]:
            rec = UFEGWConfig(msg=u)
            status, conf = self.get(rec)
            self._conf_list[u[UFE_CONFIG_ID]] = conf

    def _request(self, cmd: int, long_name: str = None, tr: Callable[[Message.Builder], Message.Builder] = lambda m: m) -> (Message.Status, Message):
        if self._session_token is None:
            return Message.Status(NOT_LOGGED_IN), None
        rep = self._uc.request(tr(
            self._uc.create_message()
                .set_long_name(long_name)
                .set_type(MsgType.st_system)
                .add_field(UFE_CMD, Message.Status(cmd))
        ))
        return rep[UFE_RESPONSE_CODE], rep

    @property
    def config_list(self):
        """Property that gets cached configuration list
        :returns UFEGW cached configuration list"""
        return self._conf_list

    def __getitem__(self, config_id):
        """Indexer to get a configuration by id
        :arg config_id configuration ID
        :returns UFEGWConfig object if found, otherwise None"""
        return self._conf_list.get(config_id, None)

    def get(self, conf: UFEGWConfig) -> (Message.Status, Optional[UFEGWConfig]):
        """Requests UFEGW configuration from UFEGW
        :arg conf UFEGWConfig object with id or name filled in to request to
        :returns a pair of UFEGW request status and filled in configuration UFEGWConfig object"""
        if conf.id is not None:
            status, rep = self._request(UFE_CMD_GET_CONFIG, "get_config_record_by_id", tr=lambda m: m.add_field(UFE_CONFIG_ID, conf.id))
        elif conf.name is not None:
            status, rep = self._request(UFE_CMD_GET_CONFIG, "get_config_record_by_name", tr=lambda m: m.add_field(UFE_CONFIG_NAME, conf.name))
        else:
            return MISSING_FIELDS, conf
        if status.status != UFE_OK:
            return status, conf
        conf.record = rep[UFE_CONFIG_RECORD]
        return status, conf

    class CommitAction:
        """UFEGW configuration commit enum"""
        COMMIT_NEW = UFE_CONFIG_COMMIT_ONLY
        REPLACE_ONLY = UFE_CONFIG_COMMIT_ONLY
        COMMIT_REPLACE_AND_LOAD = UFE_CONFIG_COMMIT_REPLACE_LOAD

    def put(self, conf: UFEGWConfig, commit_action: int) -> (Message.Status, Optional[UFEGWConfig]):
        """Saves UFEGW configuration to UFEGW
        :arg conf UFEGWConfig object to save
        :arg commit_action CommitAction enum to tell UFEGW how to save configuration
        :returns a pair of UFEGW request status and saved configuration as UFEGWConfig object"""
        if conf.name is None or conf.record is None:
            return MISSING_FIELDS, conf
        status, rep = self._request(UFE_CMD_PUT_CONFIG, "put_config_record_by_name",
                                    tr=lambda m:
                                    m.add_field(UFE_CONFIG_NAME, conf.name)
                                    .add_field(UFE_CONFIG_RECORD, conf.record)
                                    .add_field(UFE_CONFIG_COMMIT_ACTION, Message.Status(commit_action))) # why action is status here?
        if status == UFE_OK and conf.id is not None:
            self._conf_list[conf.id] = conf
        return status, conf

    def remove(self, conf: UFEGWConfig) -> (Message.Status, Optional[UFEGWConfig]):
        """Removes UFEGW configuration from UFEGW
        :arg conf UFEGWConfig object with id or name filled in to remove
        :returns a pair of UFEGW request status and saved configuration as UFEGWConfig object"""
        if conf.id is not None:
            status, rep = self._request(UFE_CMD_REMOVE_CONFIG, "remove_config_record_by_id", tr=lambda m: m.add_field(UFE_CONFIG_ID, conf.id))
            if status == UFE_OK:
                del self._conf_list[conf.id]
        elif conf.name is not None:
            status, rep = self._request(UFE_CMD_REMOVE_CONFIG, "remove_config_record_by_name", tr=lambda m: m.add_field(UFE_CONFIG_NAME, conf.name))
        else:
            return MISSING_FIELDS, conf
        return status, conf

    def load_profile(self, conf: UFEGWConfig) -> Message.Status:
        """Loads UFEGW profile
        :arg conf UFEGWConfig object with filled in name of profile to load
        :returns a pair of UFEGW request status"""
        if conf.name is None:
            return MISSING_FIELDS
        status, rep = self._request(UFE_CMD_LOAD_PROFILE, "load_profile_by_name", tr=lambda m: m.add_field(UFE_CONFIG_NAME, conf.name))
        return status


class UFEGWClient:
    """UFEGW Client class that covers most of UFEGW requests"""
    def __init__(self, connection_string_dict=None):
        """Creates UFEGW client class
        :arg connection_string_dict connection strings to pass to UFEedClient ctor"""
        self._connection_string = connection_string_dict
        self._uc: UFEedClient = UFEedClient(self._connection_string)
        self._session_token: Optional[UUID] = None
        self._services: {int, UFEGWService} = None
        self._users: Optional[UFEGWUserList] = None
        self._configuration_list: Optional[UFEGWConfigList] = None

    def __pass(self):
        pass

    def start(self, sub_func, req_func, rep_func=None):
        """Starts UFEGW
        :arg sub_func function to call for PUB/SUB
        :arg req_func function to call for REQ/REP"""
        if self._uc is None:
            self._uc = UFEedClient(self._connection_string)
        self._uc.start(sub_func, req_func, rep_func)

    def stop(self, do_not_send_logout = False):
        """Stosp UFEGW
        :arg do_not_send_logout do not send logout message during stop"""
        if self.started:
            self._uc.stop(do_not_send_logout)
            self._uc = None

    def __del__(self):
        """UFEGW client dtor: stops UFEGW first"""
        self.stop()

    @property
    def ufeed_client(self):
        """Property that gets inner UFEedClient object
        :returns inner UFEedClient object"""
        return self._uc

    @property
    def started(self):
        """Property that shows whethere UFEGW started or not"""
        return self._uc.started if self._uc is not None else False

    def _request(self, cmd: int, long_name: str = None) -> (Message.Status, Message):
        if self._session_token is None:
            return Message.Status(NOT_LOGGED_IN), None
        rep = self._uc.request(
            self._uc.create_message()
                .set_long_name(long_name)
                .set_type(MsgType.st_system)
                .add_field(UFE_CMD, Message.Status(cmd))
        )
        return rep[UFE_RESPONSE_CODE], rep

    def logon(self, user: str, passw: str) -> (Message.Status, Optional[UUID]):
        """Logs on user to UFEGW
        :arg user user ID
        :arg passw hashed user password
        :returns a pair of UFEGW request status and recent user session token"""
        rep = self._uc.request(
            self._uc.create_message()
                .set_long_name("login")
                .set_type(MsgType.st_system)
                .set_service_id(UFE_CMD_LOGIN)
                .add_field(UFE_CMD, Message.Status(UFE_CMD_LOGIN))
                .add_field(UFE_LOGIN_ID, user)
                .add_field(UFE_LOGIN_PW, passw))
        token = rep[UFE_SESSION_TOKEN]
        status: Message.Status = rep[UFE_RESPONSE_CODE]
        if token is not None:
            self._session_token = token
        return status, token

    def logout(self) -> Message.Status:
        """Logs out current logged in user from UFEGW
        :returns UFEGW request status"""
        if self._session_token is None:
            return Message.Status(NOT_LOGGED_IN)
        rep = self._uc.request(
            self._uc.create_message()
                .set_long_name("logout")
                .set_type(MsgType.st_system)
                .set_service_id(UFE_CMD_LOGOUT)
                .add_field(UFE_CMD, Message.Status(UFE_CMD_LOGOUT))
        )
        status: Message.Status = rep[UFE_RESPONSE_CODE]
        if status.status == LOGOFF_SUCCESSFUL:
            self._session_token = None
        return status

    def service_list(self, force_refresh: bool = False) -> (Message.Status, Optional[Dict[int, UFEGWService]]):
        """Gets or requests service list from UFEGW
        :arg force_refresh True to request service list from UFEGW
        :returns a pair of UFEGW request status and service dictionary {int, UFEGWService}"""
        if self._services is not None and not force_refresh:
            return Message.Status(UFE_OK), self._services
        self._services = {}
        status, rep = self._request(UFE_CMD_SERVICE_LIST, "service list")
        service_records: [Message] = rep[UFE_SERVICE_RECORDS]
        if service_records is not None:
            for service_record in service_records:
                service: UFEGWService = UFEGWService(service_record, self._uc, self._session_token)
                self._services[service.service_id * 1000000 + service.sub_service_id] = service
        return status, self._services

    def service(self, service_id: int, sub_service_id: int) -> Optional[UFEGWService]:
        """Gets chached service by service and subservice IDs
        :arg service_id service ID to find
        :arg sub_service_id subservice ID to find
        :returns found UFEGWService object or None if not found"""
        return self._services.get(service_id * 1000000 + sub_service_id, None)

    class SystemStatus:
        """System status class"""
        def __init__(self, msg: Message):
            self.total_sent: int = msg[UFE_TOTAL_SENT]
            self.total_received: int = msg[UFE_TOTAL_RECEIVED]
            self.resp_seq: int = msg[UFE_RESP_SEQ]
            self.recv_seq: int = msg[UFE_RECV_SEQ]
            self.brd_seq: int = msg[UFE_BRD_SEQ]
            self.workers: int = msg[UFE_WORKERS]
            self.instance_name: str = msg[UFE_INSTANCE_NAME]
            self.fix8pro_version: str = msg[UFE_FIX8PRO_VERSION]
            self.conf_dir: str = msg[UFE_CONF_DIR]
            self.pw_hash: str = msg[UFE_PW_HASH]
            self.total_sessions: int = msg[UFE_TOTAL_SESSIONS]
            self.active_sessions: int = msg[UFE_ACTIVE_SESSIONS]
            self.uptime: datetime = msg[UFE_UPTIME]
            self.cpu_percent: Optional[str] = msg[UFE_CPU_PERCENT]

    def system_status(self) -> (Message.Status, Optional[SystemStatus]):
        """Requests UFEGW system status
        :returns a pair of UFEGW request status and SystemStatus object"""
        if self._session_token is None:
            return Message.Status(NOT_LOGGED_IN)
        status, rep = self._request(UFE_CMD_SYSTEM_STATUS, "system_status")
        return status, UFEGWClient.SystemStatus(rep)

    def system_strings(self) -> (Message.Status, Optional[Dict[int, str]]):
        """Requests UFEGW system strings
        :returns a pair of UFEGW request status and system strings dictionary {int, str}"""
        if self._session_token is None:
            return Message.Status(NOT_LOGGED_IN)
        status, rep = self._request(UFE_CMD_SYSTEM_STRINGS, "system_strings")
        ret: {int, str} = {}
        for m in rep[UFE_SYSTEM_STRING]:
            ret[m[UFE_SYSTEM_STRING_TAG]] = m[UFE_SYSTEM_STRING]
        return status, ret

    def shutdown(self) -> Message.Status:
        """Shutdowns UFEGW
        :returns UFEGW request status"""
        if self._session_token is None:
            return Message.Status(NOT_LOGGED_IN)
        status, rep = self._request(UFE_CMD_SHUTDOWN, "shutdown")
        return status

    def kill(self) -> Message.Status:
        """Kills UFEGW - NEVER RETURNS, DO NOT USE
        :returns UFEGW request status"""
        if self._session_token is None:
            return Message.Status(NOT_LOGGED_IN)
        status, rep = self._request(UFE_CMD_KILL, "kill")
        return status

    def user_list(self, force_refresh: bool = False) -> (Message.Status, Optional[UFEGWUserList]):
        """Gets or requests user list from UFEGW
        :arg force_refresh True to request user list from UFEGW
        :returns a pair of UFEGW request status and user list UFEGWUserList object"""
        if self._users is not None and not force_refresh:
            return Message.Status(UFE_OK), self._users
        status, rep = self._request(UFE_CMD_GET_USERS, "user list")
        if status.status != UFE_OK:
            self._users = None
        else:
            self._users = UFEGWUserList(rep, self._uc, self._session_token)
        return status, self._users

    def check_logged_in_user_permission(self) -> (Message.Status, Optional[UFEGWUser]):
        """Checks logged in user permissions
        :returns a pair of UFEGW request status and current logged in user"""
        status, rep = self._request(UFE_CMD_CHKPERM, "check_logged_in_user_permission")
        if status.status != UFE_OK:
            return status, None
        ret = UFEGWUser(rep)
        ret.logged_in = True
        return status, ret

    def config_list(self, force_refresh: bool = False) -> (Message.Status, Optional[UFEGWConfigList]):
        """Gets or requests configuration list from UFEGW
        :arg force_refresh True to request configuration list from UFEGW
        :returns a pair of UFEGW request status and config list UFEGWConfigList object"""
        if self._users is not None and not force_refresh:
            return Message.Status(UFE_OK), self._configuration_list
        status, rep = self._request(UFE_CMD_GET_CONFIG_LIST, "get_config_list")
        if status.status != UFE_OK:
            self._configuration_list = None
        else:
            self._configuration_list = UFEGWConfigList(rep, self._uc, self._session_token)
        return status, self._configuration_list

    def internal_report(self):
        """Not implemented"""
        ...

    def add_sub_handler(self, sub_func: Callable[[Message], None]):
        """Adds PUB/SUB handler"""
        self._uc.add_sub_handler(sub_func)

    def remove_sub_handler(self, sub_func: Callable[[Message], None]):
        """Removes PUB/SUB handler"""
        self._uc.remove_sub_handler(sub_func)

    def add_req_handler(self, req_func: Callable[[Message], None]):
        """Adds REQ/REP handler"""
        self._uc.add_req_handler(req_func)

    def remove_req_handler(self, req_func: Callable[[Message], None]):
        """Removes REQ/REP handler"""
        self._uc.remove_req_handler(req_func)

    def add_rep_handler(self, rep_func: Callable[[Message], Message]):
        """Adds backchannel REQ/REP handler"""
        self._uc.add_rep_handler(rep_func)

    def remove_rep_handler(self, rep_func: Callable[[Message], Message]):
        """Removes backchannel REQ/REP handler"""
        self._uc.remove_rep_handler(rep_func)

