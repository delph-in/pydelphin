"""
Classes and functions for parsing and inspecting TDL.

This module makes it easy to inspect what is written on definitions in
Typed Description Language (TDL), but it doesn't interpret type
hierarchies (such as by performing unification, subsumption
calculations, or creating GLB types). That is, while it wouldn't be
useful for creating a parser, it is useful if you want to statically
inspect the types in a grammar and the constraints they apply.

"""

import re
from collections import deque, defaultdict
from itertools import chain

from delphin.exceptions import TdlError, TdlParsingError
from delphin.tfs import TypedFeatureStructure

_list_head = 'FIRST'
_list_tail = 'REST'
_diff_list_list = 'LIST'
_diff_list_last = 'LAST'


class TdlDefinition(TypedFeatureStructure):
    """
    A TdlDefinition is like a TypedFeatureStructure but each structure
    may have a list of supertypes instead of a type. It also allows for
    comments.
    """

    def __init__(self, supertypes=None, featvals=None, comment=None):
        TypedFeatureStructure.__init__(self, None, featvals=featvals)
        self.supertypes = list(supertypes or [])
        self.comment = comment

    @classmethod
    def default(cls): return TdlDefinition()

    def __repr__(self):
        return '<TdlDefinition object at {}>'.format(id(self))

    def _is_notable(self):
        """
        TdlDefinitions are notable if they define supertypes or have no
        sub-features or more than one sub-feature.
        """
        return bool(self.supertypes) or len(self._avm) != 1

    def local_constraints(self):
        cs = []
        for feat, val in self._avm.items():
            try:
                if val.supertypes and not val._avm:
                    cs.append((feat, val))
                else:
                    for subfeat, subval in val.features():
                        cs.append(('{}.{}'.format(feat, subfeat), subval))
            except AttributeError:
                cs.append((feat, val))
        return cs


class TdlConsList(TdlDefinition):
    def __repr__(self):
        return "<TdlConsList object at {}>".format(id(self))

    def values(self):
        def collect(d):
            if d is None or d.get('FIRST') is None: return []
            vals = [d['FIRST']]
            vals.extend(collect(d.get('REST')))
            return vals
        return collect(self)


class TdlDiffList(TdlDefinition):
    def __repr__(self):
        return "<TdlDiffList object at {}>".format(id(self))

    def values(self):
        def collect(d):
            if d is None or d.get('FIRST') is None: return []
            vals = [d['FIRST']]
            vals.extend(collect(d.get('REST')))
            return vals
        return collect(self.get('LIST'))


class TdlType(TdlDefinition):
    def __init__(self, identifier, definition, coreferences=None):
        TdlDefinition.__init__(self, definition.supertypes,
                               definition._avm.items(), definition.comment)
        self.identifier = identifier
        self.definition = definition
        self.coreferences = list(coreferences or [])

    def __repr__(self):
        return "<TdlType object '{}' at {}>".format(
            self.identifier, id(self)
        )

    # @property
    # def supertypes(self):
    #     return self.definition.supertypes

    # @property
    # def comment(self):
    #     return self.definition.comment




class TdlInflRule(TdlType):
    def __init__(self, identifier, affix=None, **kwargs):
        TdlType.__init__(self, identifier, **kwargs)
        self.affix = affix


break_characters = r'<>!=:.#&,[];$()^/'

_tdl_re = re.compile(
    r'("[^"\\]*(?:\\.[^"\\]*)*"'  # double-quoted "strings"
    r"|'[^ \\]*(?:\\.[^ \\]*)*"  # single-quoted 'strings
    r'|[^\s{break_characters}]+'  # terms w/o break chars
    r'|#[^\s{break_characters}]+'  # coreferences
    r'|!\w'  # character classes
    r'|:=|:\+|:<|<!|!>|\.\.\.'  # special punctuation constructs
    r'|[{break_characters}])'  # break characters
    .format(break_characters=re.escape(break_characters)),
    re.MULTILINE
)

# both ;comments and #|comments|#
_tdl_start_comment_re = re.compile(r'^\s*;|^\s*#\|')
_tdl_end_comment_re = re.compile(r'.*#\|\s*$')


def tokenize(s):
    return _tdl_re.findall(s)


def lex(stream):
    """
    Yield (line_no, event, obj)
    """
    lines = enumerate(stream)
    line_no = 0
    try:
        while True:
            block = None
            line_no, line = next(lines)
            if re.match(r'^\s*;', line):
                yield (line_no + 1, 'LINECOMMENT', line)
            elif re.match(r'^\s*#\|', line):
                block = []
                while not re.match(r'.*\|#\s*$', line):
                    block.append(line)
                    _, line = next(lines)
                block.append(line)  # also add the last match
                yield (line_no + 1, 'BLOCKCOMMENT', ''.join(block))
            elif re.match(r'^\s*$', line):
                continue
            elif re.match(r'^\s*%', line):
                block = _read_block('(', ')', line, lines)
                yield (line_no + 1, 'LETTERSET', block)
            else:
                block = _read_block('[', ']', line, lines, terminator='.')
                yield (line_no + 1, 'TYPEDEF', block)

    except StopIteration:
        if block:
            raise TdlParsingError(
                'Unexpected termination around line {}.'.format(line_no)
            )


def _read_block(in_pattern, out_pattern, line, lines, terminator=None):
    block = []
    try:
        tokens = tokenize(line)
        lvl = _nest_level(in_pattern, out_pattern, tokens)
        while lvl > 0 or (terminator and tokens[-1] != terminator):
            block.extend(tokens)
            _, line = next(lines)
            tokens = tokenize(line)
            lvl += _nest_level(in_pattern, out_pattern, tokens)
        block.extend(tokens)  # also add the last match
    except StopIteration:
        pass  # the next StopIteration should catch this so return block
    return block


def _nest_level(in_pattern, out_pattern, tokens):
    lookup = {in_pattern: 1, out_pattern: -1}
    return sum(lookup.get(tok, 0) for tok in tokens)


def parse(f):
    for line_no, event, data in lex(f):
        data = deque(data)
        try:
            if event == 'TYPEDEF':
                yield parse_typedef(data)
        except TdlParsingError as ex:
            ex.line_number = line_no
            if hasattr(f, 'name'):
                ex.filename = f.name
            raise


def parse_typedef(tokens):
    t = None
    identifier = None  # in case of StopIteration on first token
    try:
        identifier = tokens.popleft()
        assignment = tokens.popleft()
        affixes = parse_affixes(tokens)  # only for inflectional rules
        tdldef, corefs = parse_conjunction(tokens)
        # Now make coref paths a string instead of list
        corefs = _make_coreferences(corefs)
        #features = parse_conjunction(tokens)
        assert tokens.popleft() == '.'
        # :+ doesn't need supertypes
        if assignment != ':+' and len(tdldef.supertypes) == 0:
            raise TdlParsingError('Type definition requires supertypes.')
        t = TdlType(identifier, tdldef, coreferences=corefs)
    except AssertionError as ex:
        msg = 'Remaining tokens: {}'.format(list(tokens))
        #   previously used six library:
        # raise_from(TdlParsingError(msg, identifier=identifier), ex)
        #   use the following when Python2.7 support is dropped
        # raise TdlParsingError(msg, identifier=identifier) from ex
        raise TdlParsingError(msg, identifier=identifier)
    except StopIteration as ex:
        msg = 'Unexpected termination.'
        #   previously used six library:
        # raise_from(TdlParsingError(msg, identifier=identifier or '?'), ex)
        #   use the following when Python2.7 support is dropped
        # raise TdlParsingError(msg, identifier=identifier or '?') from ex
        raise TdlParsingError(msg, identifier=identifier or '?')
    return t


def parse_affixes(tokens):
    affixes = None
    if tokens[0] in ('%prefix', '%suffix'):
        affixes = []
        aff = tokens.popleft()
        while tokens[0] == '(':
            tokens.popleft()  # the '('
            affixes.append(tokens.popleft(), tokens.popleft())
            assert tokens.popleft() == ')'
    return affixes


def parse_conjunction(tokens):
    if tokens and tokens[0][:1] in ('\'"'):
        return tokens.popleft(), []  # basic string value
    supertypes = []
    features = []
    coreferences = []
    comment = None

    cls = TdlDefinition  # default type
    tokens.appendleft('&')  # this just makes the loop simpler
    while tokens[0] == '&':

        tokens.popleft()  # get rid of '&'
        feats = []
        corefs = []
        if tokens[0] == '.':
            raise TdlParsingError('"." cannot appear after & in conjunction.')

        # comments can appear after any supertype and before any avm, but let's
        # be a bit more generous and just say they can appear at most once
        #if tokens[0].startswith('"'):
        #    if comment is not None:
        #        raise TdlParsingError('Only one comment string is allowed.')
        #    comment = tokens.popleft()

        # comments aren't followed by "&", so pretend nothing happened (i.e.
        # use if, not elif)
        if tokens[0].startswith('#'):
            # coreferences don't have features, so just add it and move on
            coreferences.append((tokens.popleft(), [[]]))
            continue
        # other terms may have features or other coreferences
        elif tokens[0] == '[':
            feats, corefs = parse_avm(tokens)
        elif tokens[0] == '<':
            feats, corefs = parse_cons_list(tokens)
            cls = TdlConsList
        elif tokens[0] == '<!':
            feats, corefs = parse_diff_list(tokens)
            cls = TdlDiffList
        # elif tokens[0][:1] in ('\'"'):
        #     raise TdlParsingError('String cannot be part of a conjunction.')
        else:
            supertypes.append(tokens.popleft())

        if feats is None:
            features = None
        else:
            assert features is not None
            features.extend(feats)
        coreferences.extend(corefs)

    if features is None and cls is TdlDefinition:
        tdldef = None
    else:
        tdldef = cls(supertypes, features, comment=comment)

    return tdldef, coreferences


def parse_avm(tokens):
    # [ attr-val (, attr-val)* ]
    features = []
    coreferences = []
    assert tokens.popleft() == '['
    if tokens[0] != ']':  # non-empty AVM
        tokens.appendleft(',')  # to make the loop simpler
    while tokens[0] != ']':
        tokens.popleft()
        attrval, corefs = parse_attr_val(tokens)
        features.append(attrval)
        coreferences.extend(corefs)
    # '[', '.', '"', '/', '<', '#'
    assert tokens.popleft() == ']'
    return features, coreferences


def parse_attr_val(tokens):
    # PATH(.PATH)* val
    path = [tokens.popleft()]
    while tokens[0] == '.':
        tokens.popleft()
        path.append(tokens.popleft())
    path = '.'.join(path)  # put it back together (maybe shouldn'ta broke it)
    value, corefs = parse_conjunction(tokens)
    corefs = [(c, [[path] + p for p in ps]) for c, ps in corefs]
    return ((path, value), corefs)


def parse_cons_list(tokens):
    assert tokens.popleft() == '<'
    feats, last_path, coreferences = _parse_list(tokens, ('>', '.', '...'))
    if tokens[0] == '...':  # < ... > or < a, ... >
        tokens.popleft()
        # do nothing (don't terminate the list)
    elif tokens[0] == '.':  # e.g. < a . #x >
        tokens.popleft()
        tdldef, corefs = parse_conjunction(tokens)
        feats.append((last_path, tdldef))
        corefs = [(c, [[last_path] + p for p in ps]) for c, ps in corefs]
        coreferences.extend(corefs)
    elif len(feats) == 0:  # < >
        feats = None  # list is null; nothing can be added
    else:  # < a, b >
        feats.append((last_path, None))  # terminate the list
    assert tokens.popleft() == '>'
    return (feats, coreferences)

def parse_diff_list(tokens):
    assert tokens.popleft() == '<!'
    feats, last_path, coreferences = _parse_list(tokens, ('!>'))
    if not feats:
        # always have the LIST path
        feats.append((_diff_list_list, TdlDefinition()))
        last_path = _diff_list_list
    else:
        # prepend 'LIST' to all paths
        feats = [('.'.join([_diff_list_list, path]), val)
                 for path, val in feats]
        last_path = '{}.{}'.format(_diff_list_list, last_path)
    # always have the LAST path
    feats.append((_diff_list_last, TdlDefinition()))
    coreferences.append((None, [[last_path], [_diff_list_last]]))
    assert tokens.popleft() == '!>'
    return (feats, coreferences)


def _parse_list(tokens, break_on):
    feats = []
    coreferences = []
    path = _list_head
    while tokens[0] not in break_on:
        tdldef, corefs = parse_conjunction(tokens)
        feats.append((path, tdldef))
        corefs = [(c, [[path] + p for p in ps]) for c, ps in corefs]
        coreferences.extend(corefs)
        if tokens[0] == ',':
            path = '{}.{}'.format(_list_tail, path)
            tokens.popleft()
        elif tokens[0] == '.':
            break
    path = path.replace(_list_head, _list_tail)
    return (feats, path, coreferences)


def _make_coreferences(corefs):
    corefs = [(cr, ['.'.join(p) for p in paths]) for cr, paths in corefs]
    merged = defaultdict(list)
    unlabeled = []
    # unlabeled ones (e.g. from diff lists) don't have a coref tag, but
    # probably already have all the paths-to-unify. Labeled ones likely
    # only have one path each, so merge those with the same tag.
    for (cr, paths) in corefs:
        if cr is None:
            unlabeled.append((cr, paths))
        else:
            merged[cr].extend(paths)
    # now we can put them back together
    corefs = list(merged.items()) + unlabeled
    # just check that all have at least two paths
    if not all(len(paths) >= 2 for cr, paths in corefs):
        raise TdlError(
            'Solitary coreference: {}\n{}'
            .format(str(cr), repr(paths))
        )
    return corefs
