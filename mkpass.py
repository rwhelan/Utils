#!/usr/bin/env python

import random

secure = True

chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
#chars = [chr(i) for i in (range(97, 123) + range(65, 91) + range(48, 58))]

randomdev = open('/dev/random', 'r')
urandomdev = open('/dev/urandom', 'r')

entropy = []
keep = []

def populate_keep():
    global keep

    for val in [ord(randomdev.read(1)) >> i & 1 for i in range(7,-1,-1)]:
        val = True if val else False
        keep.append(val)


def populate_entropy():
    global entropy

    for char in urandomdev.read(1024):
        entropy.append(char)


# Maybe moar random / secure?
def sGenPassWd(length=8):
    global keep
    global entropy

    while length > 0:
        if not keep:    populate_keep()
        if not entropy: populate_entropy()

        cur_char = entropy.pop(0)
        if (cur_char in chars) and keep.pop(0):
            return cur_char+sGenPassWd(length-1)
        else:
            continue

    return ''


def qGenPassWd(length=8):
    if length:
        char = random.choice(chars)
        return char+qGenPassWd(length-1)

    return ''


if secure: GenPassWd = sGenPassWd
else:      GenPassWd = qGenPassWd

print GenPassWd(32)
