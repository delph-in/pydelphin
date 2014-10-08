import re
from collections import deque, OrderedDict
from itertools import chain
from delphin._exceptions import TdlError, TdlParsingError

break_characters = r'<>!=:.#&,[];$()^/'

tdl_re = re.compile(
    r'("[^"\\]*(?:\\.[^"\\]*)*"'  # double-quoted "strings"
    r"|'[^ \\]*(?:\\.[^ \\]*)*"  # single-quoted 'strings
    r'|[^\s{break_characters}]+'  # terms w/o break chars
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


class TdlType(object):
    def __init__(self, identifier, supertypes=None, constraints=None,
                 comment=None):
        self.identifier = identifier
        self.supertypes = set(supertypes or [])
        self.constraints = OrderedDict(constraints or [])
        self.comment = comment

    def __repr__(self):
        info = []
        if self.supertypes:
            info.append('supertypes={}'.format(sorted(self.supertypes)))
        if self.constraints:
            info.append('constraints={}'
                        .format(sorted(self.constrains.items())))
        if self.comment:
            info.append('comment={}'.format(self.comment))
        post = '' if not info else ', '.join([''] + info)
        return "TdlType('{}'{})".format(self.identifier, post)

class TdlInflRule(TdlType):
    def __init__(self, identifier, affix=None, **kwargs):
        TdlType.__init__(self, identifier, **kwargs)
        self.affix = affix


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
        supertypes, constraints, comment = parse_conjunction(tokens)
        #supertypes = parse_supertypes(tokens)
        #comment = parse_typedef_comment(tokens)
        # there may be a '&' after the comment? Or maybe not..
        #if tokens[0] == '&':
        #    tokens.popleft()

        #constraints = parse_conjunction(tokens)
        assert tokens.popleft() == '.'
        # :+ doesn't need supertypes
        if assignment != ':+' and len(supertypes) == 0:
            raise TdlParsingError('Type definition requires supertypes.')
        t = TdlType(identifier, supertypes=supertypes,
                       constraints=constraints)
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
    constraints = []
    coreferences = []
    comment = None

    tokens.appendleft('&')  # this just makes the loop simpler
    while tokens[0] == '&':

        tokens.popleft()  # get rid of '&'
        cons = []
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
            cons, corefs = parse_avm(tokens)
        elif tokens[0] == '<':
            cons, corefs = parse_cons_list(tokens)
        elif tokens[0] == '<!':
            cons, corefs = parse_diff_list(tokens)
        elif tokens[0] == '#':
            tokens.popleft()
            corefs = [(tokens.popleft(), [])]
        else:
            supertypes.append(tokens.popleft())

        constraints.extend(cons)
        coreferences.extend(corefs)

    return supertypes, constraints, comment


def parse_avm(tokens, path=None):
    # [ attr-val (, attr-val)* ]
    if path is None:
        path = []
    constraints = []
    coreferences = []
    curpath = []
    assert tokens.popleft() == '['
    tokens.appendleft(',')  # to make the loop simpler
    while tokens[0] != ']':
        assert tokens.popleft() == ','
        for cons, corefs in parse_attr_vals(tokens):
            raise Exception(cons)
            cons = [('.'.join(path + path2), val) for path2, val in cons]
            corefs = [(coref, '.'.join(path + path2)) for coref, path2 in corefs]
            constraints.extend(cons)
            corefs.extend(corefs)
    # '[', '.', '"', '/', '<', '#'
    assert tokens.popleft() == ']'
    return constraints, coreferences


def parse_attr_vals(tokens):
    # PATH(.PATH)* val
    path = [tokens.popleft()]
    while tokens[0] == '.':
        tokens.popleft()
        path.append(tokens.popleft())
    # treat string values separately so they don't become comment strings
    if tokens[0].startswith('"'):
        yield ((path, tokens.popleft()), [])
    else:
        supertypes, constraints, comment = parse_conjunction(tokens)
        for (path2, val) in constraints:
            yield ((path + path2, val), [])


def parse_cons_list(tokens):
    token = tokens.popleft()
    while token != '>':
        token = tokens.popleft()

def parse_diff_list(tokens):
    token = tokens.popleft()
    while token != '!>':
        token = tokens.popleft()


if __name__ == '__main__':
    import sys
    for x in lex(open(sys.argv[1], 'r')):
        print(x)
    #for line in sys.stdin:
    #    print(tokenize(line))
