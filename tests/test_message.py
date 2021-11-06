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
import pytest

from UPA import *
fix50 = FIX50SP2_Fields


@pytest.mark.timeout(20)
def test_message():
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
        .build() \
        .new_builder() \
        .add_field(fix50.Account.tag, "ACC1") \
        .add_group(fix50.NoAllocs.tag, g1, lambda m, grp:
            m.add_group_item(g1)
                   .set_long_name("NoAlloc")
                   .set_type(MsgType.st_fixmsg)
                   .set_seq(1)
                   .add_field(fix50.AllocAccount.tag, "ALLOC1")
                   .add_field(fix50.AllocQty.tag, 50.12345, precision=4) and
            m.add_group_item(g1)
                   .set_long_name("NoAlloc")
                   .set_type(MsgType.st_fixmsg)
                   .set_seq(3)
                   .add_field(fix50.AllocAccount.tag, "ALLOC2")
                   .add_field(fix50.AllocQty.tag, 60.654321, precision=3)
                   ) \
        .add_field(UFE_SESSION_TOKEN, uuid.UUID("ed391284-bb68-4e14-a786-3eb0387694d9"), Location.fl_system) \
        .add_field(UFE_STATUS_CODE, Message.Status(UFE_OK), Location.fl_system) \
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
    s = msg.print()
    assert len(s) != 0

    assert len(msg.fields) == 12
    assert len(msg.groups) == 2

    def _check_field(tag: int, value, pytype, fldtype: int, loc: int = Location.fl_body):
        assert msg[tag] is not None
        assert msg.fields.get(tag, None) is not None
        assert msg.groups.get(tag, None) is None
        fld1 = msg[tag]
        fld2 = msg.fields[tag]
        assert fld1 == value
        assert type(fld1) == pytype
        assert fld2.type == fldtype
        assert fld2.location == loc

    def _check_nonexistng_field(tag: int):
        assert msg[tag] is None
        assert msg.fields.get(tag, None) is None

    def _check_group(tag: int, size: int, loc: int = Location.fl_body):
        assert msg[tag] is not None
        assert msg.fields.get(tag, None) is None
        assert msg.groups.get(tag, None) is not None
        grp1 = msg[tag]
        grp2 = msg.groups[tag]
        assert type(grp1) == list
        assert len(grp2) == size
        return grp2

    def _check_nonexisting_group(tag: int):
        assert msg[tag] is None
        assert msg.fields.get(tag, None) is None
        assert msg.groups.get(tag, None) is None

    _check_field(fix50.ClOrdID.tag, "123", str, FieldType.ft_string)
    _check_nonexistng_field(fix50.OrderID.tag)
    _check_field(fix50.TransactTime.tag, now, datetime, FieldType.ft_time)
    _check_field(fix50.Price.tag, 111.22, float, FieldType.ft_double)
    _check_field(fix50.OrderQty.tag, 33, int, FieldType.ft_int)
    _check_field(fix50.PossDupFlag.tag, True, bool, FieldType.ft_bool)
    _check_field(UFE_SESSION_TOKEN, uuid.UUID("ed391284-bb68-4e14-a786-3eb0387694d9"), uuid.UUID, FieldType.ft_uuid,
                 Location.fl_system)
    _check_field(UFE_STATUS_CODE, Message.Status(UFE_OK), Message.Status, FieldType.ft_status, Location.fl_system)

    gg1 = _check_group(fix50.NoAllocs.tag, 2)
    gg2 = _check_group(fix50.NoPartyIDs.tag, 1)
    _check_nonexisting_group(fix50.NoApplIDs.tag)
    assert len(gg1[0].fields) == 2 and gg1[0].seq == 1
    assert len(gg1[1].fields) == 2 and gg1[1].seq == 3
    assert len(gg2[0].fields) == 1 and gg1[0].seq == 1
    assert len(gg2[0].groups) == 1
