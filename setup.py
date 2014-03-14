# -*- coding: utf-8 -*-
from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='addic7ed',
      version='0.1.9',
      description='A commandline access to addic7ed subtitles',
      long_description=readme(),
      url='https://github.com/BenoitZugmeyer/addic7ed-cli/',
      author='Benoît Zugmeyer',
      author_email='bzugmeyer@gmail.com',
      license='Expat',
      packages=['addic7ed'],
      install_requires=[
          'pyquery>=1.2.4',
          'requests>=2.2.1',
      ],
      entry_points={
          'console_scripts': ['addic7ed=addic7ed.__init__:main'],
      },
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=True)
