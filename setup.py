# -*- coding: utf-8 -*-
from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='addic7ed',
      version='0.1.4',
      description='A commandline access to addic7ed subtitles',
      long_description=readme(),
      url='https://github.com/BenoitZugmeyer/addic7ed-cli/',
      author='Benoît Zugmeyer',
      author_email='bzugmeyer@gmail.com',
      license='MIT',
      packages=['addic7ed'],
      install_requires=[
          'pyquery',
          'requests==0.14.1',  # 0.14.2 can't be installed through pip
      ],
      entry_points={
          'console_scripts': ['addic7ed=addic7ed.__init__:main'],
      },
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=True)
