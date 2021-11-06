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
from datetime import datetime

from UPA import *
import time


class NewOrderSingle(FIXMessage):
    class Builder(FIXMessage.Builder):
        def __init__(self,
                     price: float,
                     symbol: str,
                     quantity: float,
                     order_type: str,
                     side: str,
                     time_in_force: str,
                     cl_ord_id: str,
                     transact_time="now"):
            FIXMessage.Builder.__init__(self)
            self.add_fields([
                (COMMON_PRICE, price),
                (COMMON_SYMBOL, symbol),
                (COMMON_ORDERQTY, quantity),
                (COMMON_ORDTYPE, order_type),
                (COMMON_SIDE, side),
                (COMMON_TIMEINFORCE, time_in_force),
                (COMMON_CLORDID, cl_ord_id),
                (COMMON_TRANSACTTIME, transact_time)
            ])


class ExecutionReport(FIXMessage):
    def __init__(self,
                 msg):
        FIXMessage.__init__(self, msg)

    def fill_value(self):
        if COMMON_LASTSHARES in self.fields:
            return float(self[COMMON_PRICE]) * float(self[COMMON_LASTSHARES])
        else:
            return 0.0


if __name__ == "__main__":
    # Capture
    BHP_fills = []

    # user defined
    def subscriber_func(msg):
        if msg.longname == "ExecutionReport":
            er = ExecutionReport(msg)
            if "BHP" in er[COMMON_SYMBOL]:
                BHP_fills.append((er[COMMON_ORDERID],
                                  er[COMMON_EXECID],
                                  er.fill_value()))

    # user defined
    def requester_func(msg):
        pass


    # UFEedClient can accept a dictionary to remap the connections strings, but here we just run the default
    uc = UFEedClient()

    # pass in the user defined subscriber and responder functions, these functions handle the message responses
    uc.start(sub_func=subscriber_func, req_func=requester_func)

    # login
    print("login")
    login = uc.create_message() \
        .set_type(MsgType.st_system) \
        .set_long_name("logon") \
        .set_service_id(UFE_CMD_LOGIN) \
        .add_field(UFE_CMD, Message.Status(UFE_CMD_LOGIN)) \
        .add_field(UFE_LOGIN_ID, "davidd") \
        .add_field(UFE_LOGIN_PW, "264872bcf90c45d678dea41c91c8adbf40dcd712031db08efb52d841a1f937d9")
    response = uc.request(login)

    # prepare newordersingle message specialisation
    nosd = {"price": 10.25,
            "symbol": "BHP",
            "quantity": 100.,
            "order_type": '1',
            "side": '0',
            "time_in_force": '2',
            "cl_ord_id": "Ord01"}
    nos = NewOrderSingle.Builder(**nosd) \
        .set_long_name("NewOrderSingle") \
        .set_name("D") \
        .set_service_id(6)
    response = uc.request(nos)

    time.sleep(1)
    print("logout")

    # logout
    logout = uc.create_message() \
        .set_type(MsgType.st_system) \
        .set_long_name("logout") \
        .set_service_id(UFE_CMD_LOGOUT) \
        .add_field(UFE_CMD, Message.Status(UFE_CMD_LOGOUT))
    response = uc.request(logout)

    for i in range(100):
        print(f"... Waiting for broadcasts ...")
        time.sleep(5)
        print(BHP_fills)

    # FIX50SP2 NOS creation
    fix42 = FIX42_Fields
    fix50 = FIX50SP2_Fields

    def create_fix50_nos():
        nos = FIXMessage.Builder() \
            .set_name(fix50.MsgType.NEWORDERSINGLE) \
            .add_fields(
                [(fix50.ClOrdID.tag, "123"),
                 (fix50.TransactTime.tag, datetime.utcnow()),
                 (fix50.ExecInst.tag, fix50.ExecInst.ALL_OR_NONE),
                 (fix50.TimeInForce.tag, fix50.TimeInForce.FILL_OR_KILL),
                 (fix50.Side.tag, fix50.Side.BUY)]) \
            .add_field(fix50.OrdType.tag, fix50.OrdType.LIMIT)
        return nos
    nos5 = create_fix50_nos()
