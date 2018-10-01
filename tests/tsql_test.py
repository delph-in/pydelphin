
from datetime import datetime

import pytest

from delphin import tsql
from delphin.exceptions import TSQLSyntaxError
from delphin.util import LookaheadIterator

from .commands_test import mini_testsuite as ts0

def test_parse_query():
    parse = lambda s: tsql._parse_query(LookaheadIterator(tsql._lex(s)))
    with pytest.raises(TSQLSyntaxError):
        parse('info relations')
    with pytest.raises(TSQLSyntaxError):
        parse('set max-results 5')
    with pytest.raises(TSQLSyntaxError):
        parse('insert into item i-id values 10')

def test_parse_select():
    parse = lambda s: tsql._parse_select(LookaheadIterator(tsql._lex(s)))
    with pytest.raises(TSQLSyntaxError):
        parse('*')
    # with pytest.raises(TSQLSyntaxError):
    #     parse('i-input from item report "%s"')

    assert parse('i-input') == {
        'querytype': 'select',
        'projection': ['i-input'],
        'tables': None,
        'where': None}

    assert parse('i-input i-wf') == {
        'querytype': 'select',
        'projection': ['i-input', 'i-wf'],
        'tables': None,
        'where': None}

    assert parse('i-input i-wf from item') == {
        'querytype': 'select',
        'projection': ['i-input', 'i-wf'],
        'tables': ['item'],
        'where': None}

    assert parse('i-input mrs from item result') == {
        'querytype': 'select',
        'projection': ['i-input', 'mrs'],
        'tables': ['item', 'result'],
        'where': None}


def test_parse_select_complex_identifiers():
    parse = lambda s: tsql._parse_select(LookaheadIterator(tsql._lex(s)))
    assert parse('item:i-input') == {
        'querytype': 'select',
        'projection': ['item:i-input'],
        'tables': None,
        'where': None}

    assert parse('item:i-id@i-input') == {
        'querytype': 'select',
        'projection': ['item:i-id', 'item:i-input'],
        'tables': None,
        'where': None}

    assert parse('item:i-id@result:mrs') == {
        'querytype': 'select',
        'projection': ['item:i-id', 'result:mrs'],
        'tables': None,
        'where': None}

    assert parse('item:i-id@i-input mrs') == {
        'querytype': 'select',
        'projection': ['item:i-id', 'item:i-input', 'mrs'],
        'tables': None,
        'where': None}


def test_parse_select_where():
    parse = lambda s: tsql._parse_select(LookaheadIterator(tsql._lex(s)))
    assert parse('i-input where i-wf = 2') == {
        'querytype': 'select',
        'projection': ['i-input'],
        'tables': None,
        'where': ('==', ('i-wf', 2))}

    assert parse('i-input where i-date < 2018-01-15')['where'] == (
        '<', ('i-date', datetime(2018, 1, 15)))

    assert parse('i-input where i-date > 15-jan-2018(15:00:00)')['where'] == (
        '>', ('i-date', datetime(2018, 1, 15, 15, 0, 0)))

    assert parse('i-input where i-input ~ "Abrams"')['where'] == (
        '~', ('i-input', 'Abrams'))

    assert parse("i-input where i-input !~ 'Browne'")['where'] == (
        '!~', ('i-input', 'Browne'))

    assert parse('i-input '
                 'where i-wf = 2 & i-input ~ \'[Dd]og\'')['where'] == (
        'and', [('==', ('i-wf', 2)),
                ('~', ('i-input', '[Dd]og'))])

    assert parse('i-input '
                 'where i-id = 10 | i-id = 20 & i-wf = 2')['where'] == (
        'or', [('==', ('i-id', 10)),
               ('and', [('==', ('i-id', 20)),
                        ('==', ('i-wf', 2))])])

    assert parse('i-input '
                 'where (i-id = 10 | i-id = 20) & !i-wf = 2')['where'] == (
        'and', [('or', [('==', ('i-id', 10)),
                        ('==', ('i-id', 20))]),
                ('not', ('==', ('i-wf', 2)))])
