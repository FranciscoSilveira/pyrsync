import os
from sys import version

from distutils.core import setup


# Utility function to read the README.md file from main directory, used for
# the long_description.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='pyrsync2',
    version='0.2.6',
    description='''A Python 3 module which implements rsync binary diff
    algorithm.''',
    long_description=read('README'),
    author='Georgy Angelov, Eric Pruitt, Isis Lovecruft',
    author_email='georgyangelov@gmail.com',
    url='https://github.com/stormbreakerbg/pyrsync',
    py_modules=['pyrsync2'],
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
    packages=['pyrsync2'],
    package_dir={'pyrsync2': ''},
    package_data={'': ['README\.md']},
)
