import sys

if sys.version_info < (3, 0):
    raise RuntimeError('You need python 3 for this module.')

__author__ = "Francisco Silveira, Georgy Angelov, Eric Pruitt, Isis Lovecruft"
__date__ = "25 July 2017"
__version__ = (0, 1, 0)
__license__ = "MIT"

import hashlib

from .pyzsync import *
