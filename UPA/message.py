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
import uuid
from typing import Callable, Union, List
from datetime import datetime

from UPA.consts import UFE_FLOAT_PRECISION, UFE_OK
from UPA.ufeapi_pb2 import WireMessage, UFEField


class Location:
    """ Field location enum class """
    msg_location = UFEField.UFEFieldLocation.Value
    fl_body: int = msg_location('fl_body')
    fl_header: int = msg_location('fl_header')
    fl_trailer: int = msg_location('fl_trailer')
    fl_system: int = msg_location('fl_system')


class FieldType:
    """ Field type enum class """
    msg_field_type = UFEField.UFEFieldType.Value
    ft_unknown: int = msg_field_type('ft_unknown')
    ft_int: int = msg_field_type('ft_int')
    ft_char: int = msg_field_type('ft_char')
    ft_double: int = msg_field_type('ft_double')
    ft_string: int = msg_field_type('ft_string')
    ft_bool: int = msg_field_type('ft_bool')
    ft_time: int = msg_field_type('ft_time')
    ft_msg: int = msg_field_type('ft_msg')
    ft_uuid: int = msg_field_type('ft_uuid')
    ft_status: int = msg_field_type('ft_status')


class MsgType:
    """ Message type enum class"""
    msg_type = WireMessage.Type.Value
    st_fixmsg: int = msg_type('st_fixmsg')
    st_system: int = msg_type('st_system')
    st_servicelist: int = msg_type('st_servicelist')
    st_dictionary: int = msg_type('st_dictionary')
    st_sysstrings: int = msg_type('st_sysstrings')
    st_response: int = msg_type('st_response')
    st_error: int = msg_type('st_error')
    st_servicelog: int = msg_type('st_servicelog')
    st_heartbeat: int = msg_type('st_heartbeat')


class Epoch:
    """ Unix time epoch datetime"""
    epoch = datetime.utcfromtimestamp(0)
    time_factor = 1000000000.0


class Message:
    """
    Messages contain the System and Business information to facilitate interaction between the UFEedClient and the UFEGW.
    Message class provides mapped read-only access to the underling WireMessage object fields. For write access to underlying
    WireMessge object, use Message.Builder class
    """

    class Status:
        """ Message status field that holds integer status code"""
        def __init__(self, status: int = 0):
            self._status = status

        @property
        def status(self):
            """ Returns: status code"""
            return self._status

        def __eq__(self, other):
            """ Compares Status classes by holding status code
                Args:
                    other(Message.Status): message status to compare
                Returns: true if status codes are equal
            """
            if isinstance(other, Message.Status):
                return self.status == other.status

        def __str__(self):
            return "status(OK)" if self.status == UFE_OK else f"status({self.status})"

    class Builder:
        """
            Message builder class that provides write access to underlying WireMessage
            Sample:
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
        """

        def __init__(self, wm: WireMessage = None):
            self._wm: WireMessage = wm if wm is not None else WireMessage()

        @property
        def wire_message(self) -> WireMessage:
            """ Returns: underlying WireMessage object"""
            return self._wm

        @property
        def type(self) -> int:
            """ Returns: underlying WireMessage type"""
            return self._wm.type

        @type.setter
        def type(self, typ: int) -> None:
            """ Sets underlying WireMessage object type
                Returns: underlying WireMessage type """
            self._wm.type = typ

        @property
        def name(self) -> str:
            """ Returns: underlying WireMessage name"""
            return self._wm.name

        @name.setter
        def name(self, name: str) -> None:
            """ Sets underlying WireMessage object name
                Returns: underlying WireMessage name """
            self._wm.name = name

        @property
        def long_name(self) -> str:
            """ Returns: underlying WireMessage long name"""
            return self._wm.longname

        @long_name.setter
        def long_name(self, longname: str) -> None:
            """ Sets underlying WireMessage object long name
                Returns: underlying WireMessage long name """
            self._wm.longname = longname

        @property
        def seq(self) -> int:
            """ Returns: underlying WireMessage seq"""
            return self._wm.seq

        @seq.setter
        def seq(self, seq: int) -> None:
            """ Sets underlying WireMessage object seq
                Returns: underlying WireMessage seq """
            self._wm.seq = seq

        @property
        def service_id(self) -> int:
            """ Returns: underlying WireMessage servcie id"""
            return self._wm.service_id

        @service_id.setter
        def service_id(self, service_id: int) -> None:
            """ Sets underlying WireMessage object service id
                Returns: underlying WireMessage serviceid """
            self._wm.service_id = service_id

        @property
        def sub_service_id(self) -> int:
            """ Returns: underlying WireMessage subservice id"""
            return self._wm.subservice_id

        @sub_service_id.setter
        def sub_service_id(self, subservice_id) -> None:
            """ Sets underlying WireMessage object subservice id
                Returns: underlying WireMessage subservice id """
            self._wm.subservice_id = subservice_id

        def set_type(self, typ: int) -> "Message.Builder":
            """ Sets underlying WireMessage object type
                Returns: self """
            self.type = typ
            return self

        def set_name(self, name: str) -> "Message.Builder":
            """ Sets underlying WireMessage object name
                Returns: self """
            self.name = name
            return self

        def set_long_name(self, longname: str) -> "Message.Builder":
            """ Sets underlying WireMessage object long name
                Returns: self """
            self.long_name = longname
            return self

        def set_seq(self, seq: int) -> "Message.Builder":
            """ Sets underlying WireMessage object seq
                Returns: self """
            self.seq = seq
            return self

        def set_service_id(self, service_id: int) -> "Message.Builder":
            """ Sets underlying WireMessage object service id
                Returns: self """
            self.service_id = service_id
            return self

        def set_sub_service_id(self, subservice_id: int) -> "Message.Builder":
            """ Sets underlying WireMessage object subservice id
                Returns: self """
            self.sub_service_id = subservice_id
            return self

        def add_field(self, tag: int, val, loc: int = Location.fl_body, precision: int = UFE_FLOAT_PRECISION) -> "Message.Builder":
            """Add a single field (tag and value) to the Message.
            Args:
                tag (int): The tag component of the field.
                val (str or int or float or UUID or datetime or bool or Message.Status): The value associated with the tag.
                loc (int, optional): Defaults to fl_body
                precision (int,optional): float value decimal precision, defaults to UFE_FLOAT_PRECISION
            Returns:
                self """
            fld = self._wm.fields.add()
            fld.tag = tag
            fld.location = loc
            if type(val) == str:
                fld.sval = str(val).encode()
                fld.type = FieldType.ft_string
            elif type(val) == int:
                fld.ival = val
                fld.type = FieldType.ft_int
            elif type(val) == bool:
                fld.bval = val
                fld.type = FieldType.ft_bool
            elif type(val) == float:
                fld.fval = val
                fld.type = FieldType.ft_double
                fld.ival = precision
            elif type(val) == datetime:
                fld.ival = (int)((val - Epoch.epoch).total_seconds() * Epoch.time_factor)
                fld.type = FieldType.ft_time
            elif type(val) == Message.Status:
                fld.ival = val.status
                fld.type = FieldType.ft_status
            elif type(val) == uuid.UUID:
                fld.sval = val.bytes
                fld.type = FieldType.ft_uuid
            return self

        def add_fields(self, fields: [(int, object, int)]) -> "Message.Builder":
            """Adds a list of fields (tags, values and locations) to the Message.
            Args:
                List of tuples containing:
                fields ([(int, object, int)]) - list of (tag, val, optional loc)
            Returns:
                self """
            for f in fields:
                self.add_field(*f)
            return self

        class GroupRef:
            """ Groupd reference helpers class to fill in during group creation"""
            def __init__(self, ref: UFEField = None):
                self.ref = ref

        def add_group(self, tag: int, grp: GroupRef, tr_func: Callable[["Message.Builder", GroupRef], None] = None,
                      loc: int = Location.fl_body) -> "Message.Builder":
            """Add a group to the Message.
            Args:
                tag (int): The tag component of the field.
                grp (GroupRef): group reference to fill in
                tr_func (Callable[["Message.Builder", GroupRef]): optional function to create a group content
                loc (int, optional): Defaults to fl_body
            Returns:
                self """
            grp.ref = self._wm.fields.add()
            grp.ref.tag = tag
            grp.ref.type = FieldType.ft_msg
            grp.ref.location = loc
            if tr_func is not None:
                tr_func(self, grp)
            grp.ref.ival = len(grp.ref.mval)
            return self

        def add_group_item(self, grp_ref: GroupRef) -> "Message.Builder":
            """Add a group item to the Group.
            Args:
                grp (GroupRef): group reference to add item to
            Returns:
                self """
            wm = grp_ref.ref.mval.add()
            return Message.Builder(wm)

        def build(self) -> "Message":
            """ Builds message with remapped fields and groups
            Returns: built message"""
            return Message(self._wm)

        def print(self) -> str:
            return Message.Builder.print_wm(self._wm)

        @staticmethod
        def print_wm(wm: WireMessage, depth: int = 0) -> str:
            ret: str = f"{'   ' * depth}srvc_id={wm.service_id} subsrvc_id={wm.subservice_id} type={wm.type}" \
                       f"{f' msg={wm.name}' if len(wm.name) != 0 else ''}" \
                       f"{f' ({wm.longname})' if len(wm.longname) != 0 else ''}" \
                       f" seq={wm.seq}\n"
            f: UFEField
            for f in wm.fields:
                ret += f"{'   ' * (1 + depth)}{f.tag} ("
                if f.location == Location.fl_header:
                    ret += "hdr"
                elif f.location == Location.fl_body:
                    ret += "body"
                elif f.location == Location.fl_trailer:
                    ret += "trl"
                elif f.location == Location.fl_system:
                    ret += "sys"
                else:
                    ret += "unknown"
                ret += f"): "
                if f.type == FieldType.ft_msg:
                    ret += ''.join([Message.Builder.print_wm(wm1, depth + 1) for wm1 in f.mval])
                elif f.type == FieldType.ft_double:
                    ret += f"{Message.field_value(f)} ({f.ival})\n"
                else:
                    ret += f"{Message.field_value(f)}\n"
            return ret

        def __str__(self):
            return self.print()

    def __init__(self, wm: WireMessage = None):
        self._wm: WireMessage = wm if wm is not None else WireMessage()
        self._fields: {int, UFEField} = {}
        self._groups: {int, [Message]} = {}
        self._remap()

    @property
    def fields(self):
        """ Returns: mapped message fields """
        return self._fields

    @property
    def groups(self):
        """ Returns: mapped message groups """
        return self._groups

    @property
    def wire_message(self) -> WireMessage:
        """ Returns: underlying wire message object """
        return self._wm

    @staticmethod
    def field_value(fld: UFEField) -> Union[str, int, bool, float, datetime, "Message.Status", uuid.UUID, None]:
        """ Field or group extractor
        Args:
             fld (UFEField): field to extract value from
        Returns:
             filed or group value if found otherwise None """
        if fld is not None:
            if type(fld) == UFEField:
                if fld.type == FieldType.ft_int:
                    return fld.ival
                elif fld.type == FieldType.ft_bool:
                    return fld.bval
                elif fld.type == FieldType.ft_double:
                    return fld.fval
                elif fld.type == FieldType.ft_time:
                    return datetime.utcfromtimestamp(fld.ival / Epoch.time_factor)
                elif fld.type in (FieldType.ft_string, FieldType.ft_char):
                    return fld.sval.decode('utf-8')
                elif fld.type == FieldType.ft_status:
                    return Message.Status(fld.ival)
                elif fld.type == FieldType.ft_uuid:
                    return uuid.UUID(bytes=fld.sval)
        return None

    def __getitem__(self, tag: int) -> Union[str, int, bool, float, datetime, "Message.Status", uuid.UUID, List["Message"], None]:
        """ Field or group getter
        Args:
             tag (int): tag to get field or group for
        Returns:
             filed or group value if found otherwise None """
        fld = self._fields.get(tag, None)
        if fld is not None:
            return self.field_value(fld)
        grp = self._groups.get(tag, None)
        if grp is not None and type(grp) == list:
            return grp
        return None

    def _remap_field(self, fld: UFEField):
        if fld.type == FieldType.ft_msg:
            if fld.tag not in self._groups:
                self._groups[fld.tag] = []
            grp = self._groups[fld.tag]
            for wm in fld.mval:
                grp.append(Message(wm))
        else:
            self._fields[fld.tag] = fld

    def _remap(self):
        for fld in self._wm.fields:
            self._remap_field(fld)

    def print(self) -> str:
        return Message.Builder.print_wm(self._wm)

    def __str__(self):
        # pretty printer
        return self.print()

    __repr__ = __str__

    @property
    def type(self) -> int:
        """ Returns: underlying WireMessage type"""
        return self._wm.type

    @property
    def name(self) -> str:
        """ Returns: underlying WireMessage name"""
        return self._wm.name

    @property
    def long_name(self) -> str:
        """ Returns: underlying WireMessage long name"""
        return self._wm.longname

    @property
    def seq(self) -> int:
        """ Returns: underlying WireMessage seq"""
        return self._wm.seq

    @property
    def service_id(self) -> int:
        """ Returns: underlying WireMessage service id"""
        return self._wm.service_id

    @property
    def sub_service_id(self) -> int:
        """ Returns: underlying WireMessage subservice id"""
        return self._wm.subservice_id

    def new_builder(self) -> "Message.Builder":
        """ Returns: new message build for message modification """
        return Message.Builder(self._wm)


class SysMessage(Message):
    """ System message type """
    class Builder(Message.Builder):
        """ System message builder type """
        def __init__(self, wm: WireMessage = None):
            Message.Builder.__init__(self, wm)
            self.type = MsgType.st_system


class FIXMessage(Message):
    """ FIX message type """
    class Builder(Message.Builder):
        """ FIX message builder type """
        def __init__(self, wm: WireMessage = None):
            Message.Builder.__init__(self, wm)
            self.type = MsgType.st_fixmsg
