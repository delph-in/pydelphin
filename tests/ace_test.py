#!/usr/bin/env python -*- coding: utf-8 -*-

import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from delphin.codecs import simplemrs
import ace

ace.install()
parse_output = ace.parse('this is a foo bar sentence.', onlyMRS=True, bestparse=True)
print(parse_output)
print
m = simplemrs.loads_one(parse_output)
print(m)