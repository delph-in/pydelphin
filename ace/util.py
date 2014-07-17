#!/usr/bin/env python -*- coding: utf-8 -*-

import re, string
from collections import defaultdict
from itertools import chain, izip

def per_section(it):
    """ Read a file and yield sections using empty line as delimiter """
    section = []
    for line in it:
        if line.strip('\n'):
            section.append(line)
        else:
            yield ''.join(section)
            section = []
    # yield any remaining lines as a section too
    if section:
        yield ''.join(section)
        
def extract_between_quotations(string, double=True):
    return re.findall(r'\"(.+?)\"',string)


def grouped(iterable, n):
    return izip(*[iter(iterable)]*n)

def tokens_fromto(sentence):
    spaces = [0] + list(chain(*[(spaceloc,spaceloc+1) for spaceloc,tok \
                in enumerate(sentence) if tok == " "])) + [len(sentence)]
    for i in grouped(spaces, 2):
        yield i, sentence[i[0]:i[1]]

def remove_punct(token):
    return "".join([ch for ch in token if ch not in string.punctuation])