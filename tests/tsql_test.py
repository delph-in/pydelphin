
from datetime import datetime

import pytest

from delphin import tsql
from delphin import itsdb


def test_inspect_query():
    with pytest.raises(tsql.TSQLSyntaxError):
        tsql.inspect_query('info relations')
    with pytest.raises(tsql.TSQLSyntaxError):
        tsql.inspect_query('set max-results 5')
    with pytest.raises(tsql.TSQLSyntaxError):
        tsql.inspect_query('insert into item i-id values 10')
    with pytest.raises(tsql.TSQLSyntaxError):
        tsql.inspect_query('select *')
    assert tsql.inspect_query('select i-input') == {
        'type': 'select',
        'projection': ['i-input'],
        'relations': [],
        'condition': None}

    assert tsql.inspect_query('select i-input i-wf') == {
        'type': 'select',
        'projection': ['i-input', 'i-wf'],
        'relations': [],
        'condition': None}

    assert tsql.inspect_query('select i-input i-wf from item') == {
        'type': 'select',
        'projection': ['i-input', 'i-wf'],
        'relations': ['item'],
        'condition': None}

    assert tsql.inspect_query('select i-input mrs from item result') == {
        'type': 'select',
        'projection': ['i-input', 'mrs'],
        'relations': ['item', 'result'],
        'condition': None}


def test_parse_select_complex_identifiers():
    assert tsql.inspect_query('select item.i-input') == {
        'type': 'select',
        'projection': ['item.i-input'],
        'relations': [],
        'condition': None}

    assert tsql.inspect_query('select item.i-id result.mrs') == {
        'type': 'select',
        'projection': ['item.i-id', 'result.mrs'],
        'relations': [],
        'condition': None}

    assert tsql.inspect_query('select item.i-id i-input mrs') == {
        'type': 'select',
        'projection': ['item.i-id', 'i-input', 'mrs'],
        'relations': [],
        'condition': None}


def test_parse_select_where():
    assert tsql.inspect_query('select i-input where i-wf = 2') == {
        'type': 'select',
        'projection': ['i-input'],
        'relations': [],
        'condition': ('==', ('i-wf', 2))}

    assert tsql.inspect_query(
        'select i-input'
        ' where i-date < 2018-01-15')['condition'] == (
            '<', ('i-date', datetime(2018, 1, 15)))

    assert tsql.inspect_query(
        'select i-input'
        ' where i-date > 15-jan-2018(15:00:00)')['condition'] == (
            '>', ('i-date', datetime(2018, 1, 15, 15, 0, 0)))

    assert tsql.inspect_query(
        'select i-input'
        ' where i-input ~ "Abrams"')['condition'] == (
            '~', ('i-input', 'Abrams'))

    assert tsql.inspect_query(
        "select i-input"
        " where i-input !~ 'Browne'")['condition'] == (
            '!~', ('i-input', 'Browne'))

    assert tsql.inspect_query(
        'select i-input'
        ' where i-wf = 2 & i-input ~ \'[Dd]og\'')['condition'] == (
            'and', [('==', ('i-wf', 2)),
                    ('~', ('i-input', '[Dd]og'))])

    assert tsql.inspect_query(
        'select i-input'
        ' where i-id = 10 | i-id = 20 & i-wf = 2')['condition'] == (
            'or', [('==', ('i-id', 10)),
                   ('and', [('==', ('i-id', 20)),
                            ('==', ('i-wf', 2))])])

    assert tsql.inspect_query(
        'select i-input'
        ' where (i-id = 10 | i-id = 20) & !i-wf = 2')['condition'] == (
            'and', [('or', [('==', ('i-id', 10)),
                            ('==', ('i-id', 20))]),
                    ('not', ('==', ('i-wf', 2)))])


def test_parse_select_where_types_issue_261():
    # https://github.com/delph-in/pydelphin/issues/261
    with pytest.raises(tsql.TSQLSyntaxError):
        tsql.inspect_query('select i-id where i-wf ~ 1')
    with pytest.raises(tsql.TSQLSyntaxError):
        tsql.inspect_query('select i-id where i-input < "string"')


def test_select(mini_testsuite):
    ts = itsdb.TestSuite(mini_testsuite)
    assert list(tsql.select('i-input', ts)) == [
        ('It rained.',), ('Rained.',), ('It snowed.',)]
    assert list(tsql.select('i-input from item', ts)) == [
        ('It rained.',), ('Rained.',), ('It snowed.',)]
    assert list(tsql.select('i-input from item item', ts)) == [
        ('It rained.',), ('Rained.',), ('It snowed.',)]
    assert list(tsql.select('i-input from result', ts)) == [
        ('It rained.',), ('It snowed.',)]
    assert list(tsql.select('i-input from item result', ts)) == [
        ('It rained.',), ('It snowed.',)]
    assert list(tsql.select('i-id i-input', ts)) == [
        ('10', 'It rained.'), ('20', 'Rained.'), ('30', 'It snowed.')]
    assert list(tsql.select('i-id i-input', ts, record_class=itsdb.Row)) == [
        (10, 'It rained.'), (20, 'Rained.'), (30, 'It snowed.')]
    res = ts['result']
    assert list(tsql.select('i-id mrs', ts)) == [
        ('10', res[0]['mrs']), ('30', res[1]['mrs'])]
    with pytest.raises(tsql.TSQLSyntaxError):
        tsql.select('*', ts)
    # assert list(tsql.select('* from item', ts, cast=True)) == list(ts['item'])


def test_select_where(mini_testsuite):
    ts = itsdb.TestSuite(mini_testsuite)
    assert list(tsql.select('i-input where i-input ~ "It"', ts)) == [
        ('It rained.',), ('It snowed.',)]
    assert list(tsql.select('i-input where i-input ~ "It" or i-id = 20', ts)) == [
        ('It rained.',), ('Rained.',), ('It snowed.',)]
    assert list(tsql.select('i-input where i-date >= 2018-02-01', ts)) == [
        ('It rained.',), ('Rained.',), ('It snowed.',)]
    assert list(tsql.select('i-input where readings > 0', ts)) == [
        ('It rained.',), ('It snowed.',)]


def test_select_where_types_issue_261(mini_testsuite):
    # https://github.com/delph-in/pydelphin/issues/261
    ts = itsdb.TestSuite(mini_testsuite)
    with pytest.raises(tsql.TSQLError):
        tsql.select('i-id where i-id ~ "regex"', ts)
    with pytest.raises(tsql.TSQLError):
        tsql.select('i-id where i-input < 1', ts)
    with pytest.raises(tsql.TSQLError):
        tsql.select('i-id where i-input = 1', ts)


# def test_Relations_path(simple_relations):
#     r = tsdb.Relations.from_string(simple_relations)
#     assert r.path('item', 'result') == [('parse', 'i-id'), ('result', 'parse-id')]
#     assert r.path('parse', 'item') == [('item', 'i-id')]
#     assert r.path('item+parse', 'result') == [('result', 'parse-id')]
#     assert r.path('item', 'parse+result') == [('parse', 'i-id')]
#     assert r.path('parse', 'parse') == []
#     assert r.path('item+parse', 'parse+result') == [('result', 'parse-id')]
#     with pytest.raises(KeyError):
#         r.path('foo', 'result')
#     with pytest.raises(KeyError):
#         r.path('item', 'bar')
#     with pytest.raises(tsdb.TSDBError):
#         r.path('item', 'fold')

