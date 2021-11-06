#!/usr/bin/env python
#--------------------------------------------------------------------------------------------
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
#--------------------------------------------------------------------------------------------
import argparse
import datetime
import re


def main():
    #CLI Parsing
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description="Generates constants for Python UFEedclient. "
                                                "Omitting optional arguments will look for files"
                                                " in current directory.")
    parser.add_argument("--fix", help="specify fix fields path (usually for file field.hpp)")
    parser.add_argument("--ufe", help="specify ufe consts path (usually for file ufeconsts.hpp)")

    fix_path = "field.hpp"
    ufe_path = "ufeconsts.hpp"

    args = parser.parse_args()
    if args.fix:
        fix_path = args.fix
    if args.ufe:
        ufe_path = args.ufe

    #Open the files
    ufef = open(ufe_path, "r") #ufe file
    fixf = open(fix_path, "r") #fix file
    of = open("consts.py", "w") #output file to be written

    #Register cleanup of open files upon script termination
    import atexit
    @atexit.register
    def close_files():
        ufef.close()
        fixf.close()
        of.close()

    #Start scanning input files and writing output file
    of.write(f"# THIS FILE HAS BEEN AUTOGENERATED ON {datetime.datetime.now()} BY {__file__}\n\n")
    of.write(f"# UFE CONSTS\n")
    d_offsets = {}
    for line in ufef:
        #eg. constexpr int64_t fix8_status(int64_t src) { return src + 70000; }
        offset_line = re.match(r"constexpr\s*int64_t\s*(.*)\(.*([0-9]{5});.*", line)
        if offset_line:
            d_offsets[offset_line.group(1)] = int(offset_line.group(2))

        #eg. const int64_t session_flag_report { 0 };
        no_offsets_line_value = re.match(r"const int64_t (\S*)\s*{\s*(\d+)\s.*", line)
        if no_offsets_line_value:
            s = no_offsets_line_value.group(1).upper() + " = " + no_offsets_line_value.group(2)
            of.write(s + '\n')

        #eg. const int64_t ufe_all_services { 0x1ffff };
        no_offsets_line_value_hex = re.match(r"const int64_t (\S*)\s*{\s*(0[xX][0-9a-fA-F]+)\s.*", line)
        if no_offsets_line_value_hex:
            s = no_offsets_line_value_hex.group(1).upper() + " = " + no_offsets_line_value_hex.group(2)
            of.write(s + '\n')

        #eg. const int64_t fix8_ok { fix8_status(0) };
        add_offset_line_value = re.match(r"const int64_t (\S*)\s*{\s*(.*)\(([0-9]*)\)", line)
        if add_offset_line_value:
            offset = d_offsets[add_offset_line_value.group(2)]
            s = add_offset_line_value.group(1).upper() + " = " + str(offset + int(add_offset_line_value.group(3)))
            of.write(s + '\n')
    of.write("UFE_FLOAT_PRECISION = 2\n")

    #Write UFEGW connection defaults
    of.write(f"\n# UFEGW CONSTS\n")
    of.write("SUBSCRIBER = 'subscriber'\n")
    of.write("SUBSCRIBER_DEFAULT = 'tcp://127.0.0.1:55745'\n")
    of.write("REQUESTER = 'requester'\n")
    of.write("REQUESTER_DEFAULT = 'tcp://127.0.0.1:55746'\n")
    of.write("PUBLISHER = 'publisher'\n")
    of.write("PUBLISHER_DEFAULT = 'tcp://*:55747'\n")
    of.write("RESPONDER = 'responder'\n")
    of.write("RESPONDER_DEFAULT = 'tcp://*:55748'\n")
    of.write("SUBSCRIBER_TOPIC = 'subscribertopic'\n")
    of.write("SUBSCRIBER_TOPIC_DEFAULT = 'ufegw-publisher'\n")
    of.write("REQUESTER_TOPIC = 'requestertopic'\n")
    of.write("REQUESTER_TOPIC_DEFAULT = 'ufegw-responder'\n")
    of.write("PUBLISHER_TOPIC = 'publishertopic'\n")
    of.write("PUBLISHER_TOPIC_DEFAULT = 'ufeedclient-publisher'\n")
    of.write("RESPONDER_TOPIC = 'respondertopic'\n")
    of.write("RESPONDER_TOPIC_DEFAULT = 'ufeedclient-responder'\n")

    fix_additional_symbols = {
        "COMMON_LASTSHARES": 32,
        "COMMON_NORELATEDSYM": 146,    
        "COMMON_EXECTYPE": 150,
        "COMMON_LEAVESQTY": 151,
        "COMMON_NOMDENTRIES": 268,
        "COMMON_MDUPDATEACTION": 279,
        "COMMON_MDREQID": 262,
        "COMMON_SUBSCRIPTIONREQUESTTYPE": 263,
        "COMMON_MARKETDEPTH": 264,
        "COMMON_NOMDENTRYTYPES": 267,
        "COMMON_MDENTRYTYPE": 269,
        "COMMON_MDENTRYPX": 270,
        "COMMON_CXLREJRESPONSETO": 434
    }

    # sort the dictionary
    fix_additional_symbols = sorted(fix_additional_symbols.items(), key=lambda kv: kv[1])

    of.write(f"\n# FIX CONSTS\n")
    if fix_additional_symbols: fix_additional = fix_additional_symbols.pop(0)
    for line in fixf:
        #eg. const f8String Common_MsgType_HEARTBEAT("0");
        common_line = re.match(r"const .* (Common.*)\((\S*)\).*", line)
        if common_line:
            try:
                while (int(common_line.group(2).strip('"').strip("'")) > int(fix_additional[1])):
                    s = f"{fix_additional[0]} = {fix_additional[1]}"

                    if fix_additional[0]: of.write(s + '\n')
                    if fix_additional_symbols:
                        fix_additional = fix_additional_symbols.pop(0)
                    else:
                        fix_additional = ("", common_line.group(2))
            # this means common_line.group(2) is not an integer
            except ValueError:
                pass
            s = common_line.group(1).upper() + " = " + common_line.group(2)
            of.write(s + '\n')


if __name__ == '__main__':
    main()