import sys

if sys.version_info < (3, 0):
    raise RuntimeError('You need python 3 for this module.')

__author__ = "Georgy Angelov, Isis Lovecruft"
__date__ = "19 Jun 2013"
__version__ = (0, 2, 6)
__license__ = "MIT"

import hashlib

from .pyrsync2 import *
