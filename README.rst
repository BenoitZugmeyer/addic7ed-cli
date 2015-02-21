============
addic7ed-cli
============

This is a little command-line utility to fetch subtitles from addic7ed.

**Support addic7ed**, donate_!

Install
=======

Latest
------

Install latest development version with::

    $ pip install https://github.com/BenoitZugmeyer/addic7ed-cli/archive/master.zip

ArchLinux
---------

An `AUR package`_ is waiting for you.


Usage
=====

Example, if you speak french and english::

    $ addic7ed -l french -l english The.Serie.S02E23.MDR.mkv


Help::

    $ addic7ed --help


Authentification
================

You can login with your addic7ed.com identifiers to increase your daily
download quota:

* Anonymous users are limited to 15 downloads per 24 hours on their IP
  address

* Registered users are limited to 40

* VIPs get 80 downloads (please consider donating)

Configuration file
==================

You can store frequently used options in a configuration file. Create a
file at :code:`~/.config/addic7ed` (Linux, OSX) or :code:`%APPDATA%/config` (Windows),
and it will be parsed using the Python ConfigParser (see example below).
It can contain three sections:

* [flags], to set a flag (verbose, hearing-impaired, overwrite, ignore,
  batch or brute-batch)

* [languages], to list prefered languages

* [session], the session to use for authentification

Example::

    [flags]
    hearing-impaired = no
    batch

    [languages]
    french
    english

    [session]
    abcdef

Video organizer
===============

video-organizer_ format is supported. If a "filelist" file is next to an
episode, it will use it to extract its real name and forge the good
query.

.. _donate: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=EC7EPAVR5MXV6&submit.x=29&submit.y=10
.. _aur package: https://aur.archlinux.org/packages/addic7ed-cli
.. _video-organizer: https://github.com/JoelSjogren/video-organizer
