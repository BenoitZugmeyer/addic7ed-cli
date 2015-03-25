from __future__ import print_function

try:
    # python2
    input = raw_input
    basestring = basestring

    def encode(s):
        return s.encode('utf8')
except:
    # python3
    basestring = str
    input = input

    def encode(s):
        return s

echo = print
