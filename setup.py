from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize

extensions = [
    Extension("ufeedclient",  sources = ["build_tmp/ufeedclient.pyx"])
]

setup(
  name = 'ufeedclient',
        ext_modules = cythonize(extensions) 
)