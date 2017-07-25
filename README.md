===============================
#pyrsync2
===============================
This is a fork of the `pyrsync` package with some changes such as:

    - The functions `blockchecksums` and `rsyncdelta` are now generators
      which make it easier to send through the network
    - Some unittests are added
    - Implementation changes (uses bytearray instead of a deque, faster hash lookup etc.)
    - The block size is no longer in the delta itself, it needs to be passed
      to the patchstream function
    - Does not use try/except for programming logic

It's a Python 3 only package!

pyrsync2 is a Python module which implements the [rsync algorithm] [1],
written in pure Python. It *is not* a wrapper for rsync, but a set of
functions which apply full rsync functionality through Python.

The majority of the code for this module is taken from [Eric Pruitt's
post at ActiveState] [2]. It was orginally licensed under an [MIT license]
[3], and this license has been kept wthout modifications.

## Installation
--------------------------------
You need to have PIP:

    $ sudo pip install pyrsync2

## Use
--------------------------------
An example use case for this module:

    # On the system containing the file that needs to be patched
    >>> import pyrsync2
    >>> unpatched = open("unpatched.file", "rb")
    >>> hashes = pyrsync2.blockchecksums(unpatched)

    # On the remote system after having received hashes
    >>> import pyrsync2
    >>> patchedfile = open("patched.file", "rb")
    >>> delta = pyrsync2.rsyncdelta(patchedfile, hashes)

    # System with the unpatched file after receiving delta
    >>> unpatched.seek(0)
    >>> save_to = open("locally-patched.file", "wb")
    >>> pyrsync2.patchstream(unpatched, save_to, delta)

[1]: http://samba.anu.edu.au/rsync/ "Andrew Tridgell and Paul Mackerras. The rsync algorithm. Technical Report TR-CS-96-05, Canberra 0200 ACT, Australia, 1996."
[2]: https://code.activestate.com/recipes/577518-rsync-algorithm/ "Rsync Algorithm (Python Recipe)"
[3]: http://www.opensource.org/licenses/mit-license.php "OSI MIT License"
