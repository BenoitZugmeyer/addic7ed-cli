from __future__ import print_function

try:
    # python2
    input = raw_input
    basestring = basestring

    def encode(s):
        return s.encode('utf8')

    PY2 = True
except:
    # python3
    basestring = str
    input = input

    def encode(s):
        return s

    PY2 = False



import sys

if not PY2 and sys.stdout.encoding != "UTF-8":
    def echo(arg=""):
        print(arg.encode(sys.stdout.encoding, errors="replace").decode(sys.stdout.encoding))
else:
    def echo(arg=""):
        print(arg)
