# -*- coding: utf-8 -*-

import pytest

from delphin import predicate


def test_split():
    split = predicate.split
    # normalized and string type
    assert split('_dog_n_1') == split('"_dog_n_1_rel"') == ('dog', 'n', '1')
    # some odd variations (some are not strictly well-formed)
    assert split('_24/7_a_1_rel') == ('24/7', 'a', '1')
    assert split('_a+bit_q_rel') == ('a+bit', 'q', None)
    assert split('_A$_n_1_rel') == ('A$', 'n', '1')
    assert split('_only_child_n_1_rel') == ('only_child', 'n', '1')
    # also (attempt to) split abstract predicates
    assert split('pron_rel') == ('pron', None, None)
    assert split('udef_q_rel') == ('udef', 'q', None)
    assert split('coord') == ('coord', None, None)
    assert split('some_relation') == ('some', None, 'relation')


def test_create():
    create = predicate.create
    assert create('dog', 'n', '1') == '_dog_n_1'
    assert create('some', 'q') == '_some_q'
    with pytest.raises(TypeError):
        create('pron')
    with pytest.raises(predicate.PredicateError):
        create('lemma', 'b')
    with pytest.raises(predicate.PredicateError):
        create('lemma space', 'a')
    with pytest.raises(predicate.PredicateError):
        create('lemma', 'a', 'sense space')


def test_normalize():
    nps = predicate.normalize
    assert nps('pron_rel') == 'pron'
    assert nps('pron_rel_rel') == 'pron_rel'  # i hope nobody does this
    assert nps('"udef_q_rel"') == 'udef_q'
    assert nps('\'udef_q_rel') == 'udef_q'
    assert nps('_dog_n_1_rel') == '_dog_n_1'
    assert nps('_DELPH-IN_n_1') == '_delph-in_n_1'


def test_is_valid():
    ivps = predicate.is_valid
    # valid
    assert ivps('pron_rel')
    assert ivps('\'pron_rel')  # single open qoute
    assert ivps('"pron_rel"')  # surrounding double-quotes
    assert ivps('udef_q_rel')
    assert ivps('"_dog_n_1_rel"')
    assert ivps('"_ad+hoc_a_1_rel"')
    assert ivps('"_look_v_up-at_rel"')
    assert ivps('_24/7_a_1_rel')
    assert ivps('_a+bit_q_rel')
    assert ivps('_A$_n_1_rel')
    assert ivps('coord')
    assert ivps('_dog_n_1')
    assert ivps('_dog_n')
    # invalid
    assert not ivps('_dog_rel')
    assert not ivps('_dog_1_rel')
    assert not ivps('_only_child_n_1_rel')


def test_is_surface():
    is_s = predicate.is_surface
    # valid
    assert not is_s('pron_rel')
    assert not is_s('\'pron_rel')  # single open qoute
    assert not is_s('"pron_rel"')  # surrounding double-quotes
    assert not is_s('udef_q')
    assert is_s('"_dog_n_1_rel"')
    assert is_s('"_ad+hoc_a_1_rel"')
    assert is_s('"_look_v_up-at_rel"')
    assert is_s('_24/7_a_1_rel')
    assert is_s('_a+bit_q_rel')
    assert is_s('_A$_n_1_rel')
    assert not is_s('coord')
    assert is_s('_dog_n_1')
    assert is_s('_dog_n')
    # invalid
    assert not is_s('_dog_rel')
    assert not is_s('_dog_1_rel')
    assert not is_s('_only_child_n_1_rel')
    assert not is_s('_a space_n_1')


def test_is_abstract():
    is_a = predicate.is_abstract
    # valid
    assert is_a('pron_rel')
    assert is_a('\'pron_rel')  # single open qoute
    assert is_a('"pron_rel"')  # surrounding double-quotes
    assert is_a('udef_q')
    assert is_a('coord')
    assert not is_a('"_dog_n_1_rel"')
    # invalid
    assert not is_a('a space_n_1')
