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
        if event == 'TYPEDEF':
            yield parse_typedef(data)

def parse_typedef(tokens):
    t = None
    try:
        identifier = tokens.popleft()
        assignment = tokens.popleft()
        affix = parse_affix(tokens)  # only for inflectional rules
        supertypes = parse_supertypes(tokens)
        # :+ doesn't need supertypes
        if assignment != ':+' and len(supertypes) == 0:
            raise TdlParsingError('Type definition requires supertypes.')
        comment = parse_typedef_comment(tokens)

        constraints = parse_conjunction(tokens)
        assert tokens.popleft() == '.'
        t = TdlType(identifier, supertypes=supertypes,
                       constraints=constraints)
    except StopIteration:
        raise TdlParsingError('Unexpected termination.')
    return t

def parse_affix(tokens):
    affixes = None
    if tokens[0] in ('%prefix', '%suffix'):
        affixes = []
        aff = tokens.popleft()
        while tokens[0] == '(':
            tokens.popleft()  # the '('
            affixes.append(tokens.popleft(), tokens.popleft())
            assert tokens.popleft() == ')'
    return affixes

def parse_supertypes(tokens):
    supertypes = []
    while tokens[0] not in ('[', '.', '"', '/', '<', '#'):
        supertypes.append(tokens.popleft())
        if tokens[0] == '&':
            tokens.popleft()
    return supertypes

def parse_typedef_comment(tokens):
    comment = None
    if tokens[0].startswith('"'):
        comment = tokens.popleft()
    return comment

def parse_conjunction(tokens):
    avm = {}
    #assert next(tokens) == '['
    #token = next(tokens)
    #path = ''
    #level = 1
    #while level > 0:
    #    if token == '[':
    #        level += 1
    #    elif token == ']':
    #        level -= 1
    return avm

def parse_term(tokens):
    pass


if __name__ == '__main__':
    import sys
    for x in lex(open(sys.argv[1], 'r')):
        print(x)
    #for line in sys.stdin:
    #    print(tokenize(line))
