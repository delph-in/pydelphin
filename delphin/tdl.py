import re
from collections import deque, OrderedDict
from itertools import chain
from delphin._exceptions import TdlError, TdlParsingError

_list_head = 'FIRST'
_list_tail = 'REST'
_diff_list_list = 'LIST'

class TdlDefinition(object):

    __slots__ = ['supertypes', 'features', '_avm']

    def __init__(self, supertypes=None, features=None):
        self.supertypes = list(supertypes or [])
        self._avm = {}
        if isinstance(features, dict):
            features = features.items()
        for feat, val in list(features or []):
            self[feat] = val

    def __setitem__(self, key, val):
        try:
            first, rest = key.split('.', 1)
        except ValueError:
            self._avm[key] = val
        else:
            first = first.upper()  # features are case-insensitive
            try:
                subdef = self._avm[first]
            except KeyError:
                subdef = self._avm.setdefault(first, TdlDefinition())
            subdef[rest] = val

    def __getitem__(self, key):
        try:
            first, rest = key.split('.', 1)
        except ValueError:
            return self._avm[key.upper()]
        else:
            return self._avm[first.upper()][rest]


class TdlType(TdlDefinition):
    def __init__(self, identifier, supertypes=None, features=None,
                 coreferences=None, comment=None):
        TdlDefinition.__init__(self, supertypes, features)
        self.identifier = identifier
        self.coreferences = list(coreferences or [])
        self.comment = comment

    def __repr__(self):
        info = []
        if self.supertypes:
            info.append('supertypes={}'.format(self.supertypes))
        if self.features:
            info.append('features={}'
                        .format(sorted(self.features.items())))
        if self.comment:
            info.append('comment={}'.format(self.comment))
        post = '' if not info else ', '.join([''] + info)
        return "<TdlType object ('{}'{}) at {}>".format(
            self.identifier, post, id(self)
        )


class TdlInflRule(TdlType):
    def __init__(self, identifier, affix=None, **kwargs):
        TdlType.__init__(self, identifier, **kwargs)
        self.affix = affix


break_characters = r'<>!=:.#&,[];$()^/'

tdl_re = re.compile(
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
tdl_start_comment_re = re.compile(r'^\s*;|^\s*#\|')
tdl_end_comment_re = re.compile(r'.*#\|\s*$')


def tokenize(s):
    return tdl_re.findall(s)


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
        supertypes, features, corefs, comment = parse_conjunction(tokens)
        #supertypes = parse_supertypes(tokens)
        #comment = parse_typedef_comment(tokens)
        # there may be a '&' after the comment? Or maybe not..
        #if tokens[0] == '&':
        #    tokens.popleft()

        #features = parse_conjunction(tokens)
        assert tokens.popleft() == '.'
        # :+ doesn't need supertypes
        if assignment != ':+' and len(supertypes) == 0:
            raise TdlParsingError('Type definition requires supertypes.')
        t = TdlType(identifier, supertypes=supertypes, features=features,
                    comment=comment)
    except AssertionError as ex:
        msg = 'Remaining tokens: {}'.format(list(tokens))
        raise TdlParsingError(msg, identifier=identifier) from ex
    except StopIteration as ex:
        msg = 'Unexpected termination.'
        raise TdlParsingError(msg, identifier=identifier or '?') from ex
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
    supertypes = []
    features = []
    coreferences = []
    comment = None

    tokens.appendleft('&')  # this just makes the loop simpler
    while tokens[0] == '&':

        tokens.popleft()  # get rid of '&'
        feats = []
        corefs = []
        if tokens[0] == '.':
            raise TdlParsingError('"." cannot appear after & in conjunction.')

        # comments can appear after any supertype and before any avm, but let's
        # be a bit more generous and just say they can appear at most once
        if tokens[0].startswith('"'):
            if comment is not None:
                raise TdlParsingError('Only one comment string is allowed.')
            comment = tokens.popleft()

        # comments aren't followed by "&", so pretend nothing happened (i.e.
        # use if, not elif)
        if tokens[0] == '[':
            feats, corefs = parse_avm(tokens)
        elif tokens[0] == '<':
            feats, corefs = parse_cons_list(tokens)
        elif tokens[0] == '<!':
            feats, corefs = parse_diff_list(tokens)
        elif tokens[0].startswith('#'):
            corefs = [(tokens.popleft(), [])]  #FIXME: what is coref'd?
        else:
            supertypes.append(tokens.popleft())

        features.extend(feats)
        coreferences.extend(corefs)

    return supertypes, features, coreferences, comment


def parse_avm(tokens, path=None):
    # [ attr-val (, attr-val)* ]
    if path is None:
        path = []
    features = []
    coreferences = []
    curpath = []
    assert tokens.popleft() == '['
    tokens.appendleft(',')  # to make the loop simpler
    while tokens[0] == ',':
        tokens.popleft()
        attrval, corefs = parse_attr_val(tokens)
        features.append(attrval)
        corefs = [(coref, '.'.join(path + path2)) for coref, path2 in corefs]
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
    # treat string values separately so they don't become comment strings
    if tokens[0].startswith('"'):
        attrval = (path, tokens.popleft())
        return (attrval, [])
    else:
        supertypes, features, corefs, comment = parse_conjunction(tokens)
        value = TdlDefinition(supertypes, features)
        return ((path, value), corefs)  # discard comment here, i guess


def parse_cons_list(tokens):
    assert tokens.popleft() == '<'
    feats, last_path, coreferences = _parse_list(tokens, ('>', '.'))
    if tokens[0] == '.':
        # last item, e.g. REST.FIRST -> REST.REST
        supers, feats, corefs, _ = parse_conjunction(tokens)
        feats.append((last_path, TdlDefinition(supers, feats)))
        corefs = [(cr, '.'.join([last_path] + path2)) for cr, path2 in corefs]
        coreferences.extend(corefs)
    elif len(feats) == 0:
        return None
    else:
        feats.append((last_path, TdlDefinition()))
    assert tokens.popleft() == '>'
    return (feats, coreferences)

def parse_diff_list(tokens):
    assert tokens.popleft() == '<!'
    feats, last_path, coreferences = _parse_list(tokens, ('!>'))
    # prepend 'LIST' to all paths
    feats = [('.'.join([_diff_list_list, path]), val) for path, val in feats]
    if not feats:
        last_path = _diff_list_list
    feats.append((_diff_list_last, TdlDefinition()))
    coreferences.append((_diff_list_last, last_path))
    assert tokens.popleft() == '!>'
    return (feats, coreferences)


def _parse_list(tokens, break_on):
    feats = []
    coreferences = []
    path = _list_head
    while tokens[0] not in break_on:
        supers, feats, corefs, _ = parse_conjunction(tokens)
        feats.append((path, TdlDefinition(supers, feats)))
        corefs = [(cr, '.'.join([path] + path2)) for cr, path2 in corefs]
        coreferences.extend(corefs)
        if tokens[0] == ',':
            path = '{}.{}'.format(_list_tail, path)
            tokens.popleft()
        elif tokens[0] == '.':
            break
    path = path.replace(_list_head, _list_tail)
    return (feats, path, coreferences)


if __name__ == '__main__':
    import sys
    for x in lex(open(sys.argv[1], 'r')):
       print(x)
    # for line in sys.stdin:
    #    print(tokenize(line))
