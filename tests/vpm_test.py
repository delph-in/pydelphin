
from io import StringIO as S

import pytest

from delphin import vpm


def test_load(tmp_path):
    vpm.load(S('; test vpm\n'
               'a : b\n'
               ' 1 >> 2'))
    vpmfile = tmp_path / 'test.vpm'
    vpmfile.write_text('; test vpm\n'
                       'a : b\n'
                       ' 1 >> 2')
    vpm.load(vpmfile)


def test_invalid():
    with pytest.raises(vpm.VPMSyntaxError):
        vpm.load(S('~~'))
    with pytest.raises(vpm.VPMSyntaxError):
        vpm.load(S('<>'))
    with pytest.raises(vpm.VPMSyntaxError):
        vpm.load(S('event >< e'))
    with pytest.raises(vpm.VPMSyntaxError):
        vpm.load(S('a : b\n'
                   ' 1 2 >> 3'))
    with pytest.raises(vpm.VPMSyntaxError):
        vpm.load(S('a : b\n'
                   ' 1 >> 2 3'))
    with pytest.raises(vpm.VPMSyntaxError):
        vpm.load(S('a b : c d\n'
                   ' 1 >> 2'))

def test_type_map_single_rule_no_semi():
    assert vpm.load(S('event <> e')).apply('event2', {}) == ('e2', {})
    assert vpm.load(S('event >> e')).apply('event2', {}) == ('e2', {})
    assert vpm.load(S('event << e')).apply('event2', {}) == ('event2', {})
    assert vpm.load(S('event == e')).apply('event2', {}) == ('e2', {})
    assert vpm.load(S('event => e')).apply('event2', {}) == ('e2', {})
    assert vpm.load(S('event <= e')).apply('event2', {}) == ('event2', {})

    assert vpm.load(S('event <> e')).apply('event2', {}, reverse=True) == ('event2', {})
    assert vpm.load(S('event >> e')).apply('event2', {}, reverse=True) == ('event2', {})
    assert vpm.load(S('event << e')).apply('event2', {}, reverse=True) == ('event2', {})
    assert vpm.load(S('event == e')).apply('event2', {}, reverse=True) == ('event2', {})
    assert vpm.load(S('event => e')).apply('event2', {}, reverse=True) == ('event2', {})
    assert vpm.load(S('event <= e')).apply('event2', {}, reverse=True) == ('event2', {})

    assert vpm.load(S('event <> e')).apply('e2', {}) == ('e2', {})
    assert vpm.load(S('event >> e')).apply('e2', {}) == ('e2', {})
    assert vpm.load(S('event << e')).apply('e2', {}) == ('e2', {})
    assert vpm.load(S('event == e')).apply('e2', {}) == ('e2', {})
    assert vpm.load(S('event => e')).apply('e2', {}) == ('e2', {})
    assert vpm.load(S('event <= e')).apply('e2', {}) == ('e2', {})

    # It turns out variable type mappings shouldn't apply in reverse..
    # assert vpm.load(S('event <> e')).apply('e2', {}, reverse=True) == ('event2', {})
    # assert vpm.load(S('event >> e')).apply('e2', {}, reverse=True) == ('e2', {})
    # assert vpm.load(S('event << e')).apply('e2', {}, reverse=True) == ('event2', {})
    # assert vpm.load(S('event == e')).apply('e2', {}, reverse=True) == ('event2', {})
    # assert vpm.load(S('event => e')).apply('e2', {}, reverse=True) == ('e2', {})
    # assert vpm.load(S('event <= e')).apply('e2', {}, reverse=True) == ('event2', {})

    assert vpm.load(S('event <> e')).apply('e2', {}, reverse=True) == ('e2', {})
    assert vpm.load(S('event >> e')).apply('e2', {}, reverse=True) == ('e2', {})
    assert vpm.load(S('event << e')).apply('e2', {}, reverse=True) == ('e2', {})
    assert vpm.load(S('event == e')).apply('e2', {}, reverse=True) == ('e2', {})
    assert vpm.load(S('event => e')).apply('e2', {}, reverse=True) == ('e2', {})
    assert vpm.load(S('event <= e')).apply('e2', {}, reverse=True) == ('e2', {})

    assert vpm.load(S('* >> a')).apply('event2', {}) == ('a2', {})
    assert vpm.load(S('semarg << *')).apply('event2', {}) == ('event2', {})
    # assert vpm.load(S('semarg << *')).apply('a2', {}, reverse=True) == ('semarg2', {})
    assert vpm.load(S('semarg << *')).apply('a2', {}, reverse=True) == ('a2', {})


def test_type_map_multi_rule_no_semi():
    assert vpm.load(S('event <> e\nref-ind <> x')).apply('event2', {}) == ('e2', {})
    assert vpm.load(S('event <> e\nref-ind <> x')).apply('ref-ind4', {}) == ('x4', {})

    assert vpm.load(S('event >> e\nevent >> wrong')).apply('event2', {}) == ('e2', {})
    assert vpm.load(S('event >> e\ne >> wrong')).apply('event2', {}) == ('e2', {})
    assert vpm.load(S('event << wrong\nevent >> e')).apply('event2', {}) == ('e2', {})

    assert vpm.load(S('event >> e\nevent << u')).apply('event2', {}) == ('e2', {})
    # It turns out variable type mappings shouldn't apply in reverse..
    # assert vpm.load(S('event >> e\nevent << u')).apply('e2', {}, reverse=True) == ('e2', {})
    # assert vpm.load(S('event >> e\nevent << u')).apply('u2', {}, reverse=True) == ('event2', {})
    assert vpm.load(S('event >> e\nevent << u')).apply('e2', {}, reverse=True) == ('e2', {})
    assert vpm.load(S('event >> e\nevent << u')).apply('u2', {}, reverse=True) == ('u2', {})

    assert vpm.load(S('* <> *\n* >> wrong\nwrong << *')).apply('a2', {}) == ('a2', {})
    assert vpm.load(S('* <> *\n* >> wrong\nwrong << *')).apply('a2', {}, reverse=True) == ('a2', {})


def test_type_map_single_with_semi():
    pass


def test_type_map_multi_with_semi():
    pass


def test_prop_map_no_semi():
    # single feature, single bidirectional property
    v = vpm.load(S('E.TENSE : TENSE\n'
                   '  present <> pres'))
    assert v.apply('event2', {'E.TENSE': 'present'}) == ('event2', {'TENSE': 'pres'})
    assert v.apply('event2', {'E.TENSE': 'past'}) == ('event2', {})
    assert v.apply('e2', {'TENSE': 'pres'}) == ('e2', {})
    assert v.apply('e2', {'TENSE': 'pres'}, reverse=True) == ('e2', {'E.TENSE': 'present'})

    # single feature, bidirectional wildcard
    v = vpm.load(S('E.TENSE : TENSE\n'
                   '  present <> pres\n'
                   '  *       <> *'))
    assert v.apply('event2', {'E.TENSE': 'present'}) == ('event2', {'TENSE': 'pres'})
    assert v.apply('event2', {'E.TENSE': 'past'}) == ('event2', {'TENSE': 'past'})
    assert v.apply('e2', {'TENSE': 'pres'}) == ('e2', {})
    assert v.apply('e2', {'TENSE': 'pres'}, reverse=True) == ('e2', {'E.TENSE': 'present'})
    assert v.apply('e2', {'TENSE': 'past'}, reverse=True) == ('e2', {'E.TENSE': 'past'})

    # one-to-many features
    v = vpm.load(S('PNG.PN : PERS NUM\n'
                   '  1sg  <> 1 sg\n'
                   '  1pl  <> 1 pl\n'
                   '  1per <> 1 !\n'
                   '  1per << 1 *\n'
                   '  3sg  <> 3 sg\n'
                   '  *    >> ! !\n'
                   '  !    << * *'))
    assert v.apply('event2', {'PNG.PN': '1sg'}) == ('event2', {'PERS': '1', 'NUM': 'sg'})
    assert v.apply('event2', {'PNG.PN': '1pl'}) == ('event2', {'PERS': '1', 'NUM': 'pl'})
    assert v.apply('event2', {'PNG.PN': '1per'}) == ('event2', {'PERS': '1'})
    assert v.apply('event2', {'PNG.PN': '4du'}) == ('event2', {})
    assert v.apply('e2', {'PERS': '1', 'NUM': 'sg'}, reverse=True) == ('e2', {'PNG.PN': '1sg'})
    assert v.apply('e2', {'PERS': '1', 'NUM': 'pl'}, reverse=True) == ('e2', {'PNG.PN': '1pl'})
    assert v.apply('e2', {'PERS': '1'}, reverse=True) == ('e2', {'PNG.PN': '1per'})
    assert v.apply('e2', {'PERS': '1', 'NUM': 'du'}, reverse=True) == ('e2', {'PNG.PN': '1per'})
    assert v.apply('e2', {'PERS': '4', 'NUM': 'du'}, reverse=True) == ('e2', {})

    # var-type conditioned wildcard
    v = vpm.load(S('E.TENSE : TENSE\n'
                   '  untensed << [e]'))
    assert v.apply('event2', {'E.TENSE': 'present'}) == ('event2', {})
    assert v.apply('e2', {}, reverse=True) == ('e2', {'E.TENSE': 'untensed'})
    assert v.apply('e2', {'TENSE': 'bogus'}, reverse=True) == ('e2', {})
    assert v.apply('x4', {}, reverse=True) == ('x4', {})

    # many-to-one features
    v = vpm.load(S('E.ASPECT.SOON E.ASPECT.EVER E.ASPECT.ALREADY : TENSE\n'
                   '  bool bool +    <> past\n'
                   '  bool +    bool <> nonpresent\n'
                   '  +    bool bool <> fut'))
    assert v.apply('event2', {'E.ASPECT.SOON': 'bool', 'E.ASPECT.EVER': 'bool', 'E.ASPECT.ALREADY': '+'}) == ('event2', {'TENSE': 'past'})
    assert v.apply('event2', {'E.ASPECT.SOON': 'bool', 'E.ASPECT.EVER': '+', 'E.ASPECT.ALREADY': 'bool'}) == ('event2', {'TENSE': 'nonpresent'})
    assert v.apply('event2', {'E.ASPECT.SOON': '+', 'E.ASPECT.EVER': 'bool', 'E.ASPECT.ALREADY': 'bool'}) == ('event2', {'TENSE': 'fut'})
    assert v.apply('e2', {'TENSE': 'past'}, reverse=True) == ('e2', {'E.ASPECT.SOON': 'bool', 'E.ASPECT.EVER': 'bool', 'E.ASPECT.ALREADY': '+'})
    assert v.apply('e2', {'TENSE': 'nonpresent'}, reverse=True) == ('e2', {'E.ASPECT.SOON': 'bool', 'E.ASPECT.EVER': '+', 'E.ASPECT.ALREADY': 'bool'})
    assert v.apply('e2', {'TENSE': 'fut'}, reverse=True) == ('e2', {'E.ASPECT.SOON': '+', 'E.ASPECT.EVER': 'bool', 'E.ASPECT.ALREADY': 'bool'})

def test_prop_map_with_semi():
    pass
