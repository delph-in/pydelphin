#!/usr/bin/env python -*- coding: utf-8 -*-

import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from ace import parse

print parse('this is a foo bar sentence.', onlyMRS=True, bestparse=True)