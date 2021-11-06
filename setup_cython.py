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
import os
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

FILES = ("consts", "message", "ufeapi_pb2", "ufeedclient", "ufegwclient")
FIX_VERSIONS = ("40", "41", "42", "43", "44", "50", "50sp1", "50sp2")
BUILD_TMP = ".build"
os.chdir(BUILD_TMP)
exts = [Extension(f"UPA.{f}", sources=[f"src/{f}.pyx"]) for f in FILES]
exts.extend(Extension(f"UPA.ufe_py_fields_fix{f}", sources=[f"src/ufe_py_fields_fix{f}.pyx"], extra_compile_args=["-fno-var-tracking-assignments"]) for f in FIX_VERSIONS)
setup(name='UPA',
      ext_modules=cythonize(exts,
                            compiler_directives={'language_level': '3'}
                            ),
      version="21.6.1")
