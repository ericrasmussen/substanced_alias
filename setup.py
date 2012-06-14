__version__ = '1.0a'

import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

setup(name='substanced_alias',
      version=__version__,
      description='Plugin for substanced CMS to create aliases for resources',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        'Intended Audience :: Developers',
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        ],
      keywords='substanced plugin zodb resource aliases',
      author='Eric Rasmussen',
      author_email='eric@chromaticleaves.com',
      url='http://python.chromaticleaves.com/docs/substanced_alias/',
      license='FreeBSD',
      packages=['substanced_alias'],
      test_suite='substanced_alias.tests',
      include_package_data=True,
      zip_safe=False,
      tests_require=['pkginfo', 'nose'],
      install_requires=['substanced'],
)
