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
import re
import os
import shutil
import glob

class Builder:
    BUILD_TMP = ".build"
    FILES = ("consts", "message", "ufeapi_pb2", "ufeedclient", "ufegwclient")
    FIX_VERSIONS = ("40", "41", "42", "43", "44", "50", "50sp1", "50sp2")

    def __init__(self, ufeed_path):
        os.makedirs(Builder.BUILD_TMP, exist_ok=True)
        os.makedirs(os.path.join(Builder.BUILD_TMP, "UPA"), exist_ok=True)
        os.makedirs(os.path.join(Builder.BUILD_TMP, "src"), exist_ok=True)
        for f in Builder.FILES:
            shutil.copyfile(f"{ufeed_path}/{f}.py", f"{Builder.BUILD_TMP}/src/{f}.pyx")
        for f in Builder.FIX_VERSIONS:
            shutil.copyfile(f"{ufeed_path}/ufe_py_fields_fix{f}.py", f"{Builder.BUILD_TMP}/src/ufe_py_fields_fix{f}.pyx")
        shutil.copyfile(f"{ufeed_path}/__init__.py", f"{Builder.BUILD_TMP}/UPA/__init__.py")
        shutil.copyfile(f"{ufeed_path}/../tests/test_message.py", f"{Builder.BUILD_TMP}/test_message.py")
        shutil.copyfile(f"{ufeed_path}/../tests/test_ufeedclient.py", f"{Builder.BUILD_TMP}/test_ufeedclient.py")
        shutil.copyfile(f"{ufeed_path}/../tests/test_ufegwclient.py", f"{Builder.BUILD_TMP}/test_ufegwclient.py")
        shutil.copyfile(f"{ufeed_path}/../requirements.txt", f"{Builder.BUILD_TMP}/requirements.txt")

    def build(self):
        os.system('python setup_cython.py build_ext --inplace')
        # This means we're in a *nix environment

    def cleanup(self):
        shutil.rmtree(os.path.join(Builder.BUILD_TMP, "src"))
        shutil.rmtree(os.path.join(Builder.BUILD_TMP, "build"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Builds ufeedclient into binary library.")
    parser.add_argument("--dir", nargs="?", default="UPA", help="specify path of ufeedclient module")
    args = parser.parse_args()
    builder = Builder(args.dir)
    builder.build()
    builder.cleanup()
