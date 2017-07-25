import os
from sys import version

from distutils.core import setup


# Utility function to read the README.md file from main directory, used for
# the long_description.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='pyzsync',
    version='0.1',
    description='''A Python 3 module which implements the zsync binary
    diff algorithm.''',
    #long_description=read('README'),
    author='Francisco Silveira, Georgy Angelov, Eric Pruitt, Isis Lovecruft',
    author_email='franciscosilveira463@gmail.com',
    url='https://github.com/FranciscoSilveira/pyzsync',
    py_modules=['pyzsync'],
    license=['MIT'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Security :: Cryptography',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Archiving',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Archiving :: Compression', ],
    packages=['pyzsync'],
    package_dir={'pyzsync': ''},
    package_data={'': ['README\.md']},
)
