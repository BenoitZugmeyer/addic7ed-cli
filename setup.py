# -*- coding: utf-8 -*-
from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='addic7ed-cli',
      version='1.3',
      description='A commandline access to addic7ed subtitles',
      long_description=readme(),
      url='https://github.com/BenoitZugmeyer/addic7ed-cli/',
      author='Benoît Zugmeyer',
      author_email='bzugmeyer@gmail.com',
      license='Expat',
      packages=['addic7ed_cli'],
      install_requires=[
          'pyquery>=1.2.4',
          'requests>=2.2.1',
      ],
      entry_points={
          'console_scripts': ['addic7ed=addic7ed_cli.__init__:main'],
      },
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=True,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: MIT License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Topic :: Multimedia',
      ],
      )
