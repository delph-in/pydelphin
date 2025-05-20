import textwrap

from delphin.tdl._exceptions import TDLError
from delphin.tdl._model import (
    AVM,
    BlockComment,
    Conjunction,
    ConsList,
    Coreference,
    DiffList,
    FileInclude,
    InstanceEnvironment,
    LetterSet,
    LineComment,
    Regex,
    String,
    Term,
    TypeDefinition,
    TypeEnvironment,
    TypeIdentifier,
    WildCard,
    _Environment,
    _ImplicitAVM,
    _MorphSet,
)

# Values for serialization
_base_indent = 2  # indent when an AVM starts on the next line
_max_inline_list_items = 3  # number of list items that may appear inline
_line_width = 79  # try not to go beyond this number of characters

# Serialization helpers

def format(obj, indent=0):
    """
    Serialize TDL objects to strings.

    Args:
        obj: instance of :class:`Term`, :class:`Conjunction`, or
            :class:`TypeDefinition` classes or subclasses
        indent (int): number of spaces to indent the formatted object
    Returns:
        str: serialized form of *obj*
    Example:
        >>> conj = tdl.Conjunction([
        ...     tdl.TypeIdentifier('lex-item'),
        ...     tdl.AVM([('SYNSEM.LOCAL.CAT.HEAD.MOD',
        ...               tdl.ConsList(end=tdl.EMPTY_LIST_TYPE))])
        ... ])
        >>> t = tdl.TypeDefinition('non-mod-lex-item', conj)
        >>> print(format(t))
        non-mod-lex-item := lex-item &
          [ SYNSEM.LOCAL.CAT.HEAD.MOD < > ].
    """
    if isinstance(obj, TypeDefinition):
        return _format_typedef(obj, indent)
    elif isinstance(obj, Conjunction):
        return _format_conjunction(obj, indent)
    elif isinstance(obj, Term):
        return _format_term(obj, indent)
    elif isinstance(obj, _MorphSet):
        return _format_morphset(obj, indent)
    elif isinstance(obj, _Environment):
        return _format_environment(obj, indent)
    elif isinstance(obj, FileInclude):
        return _format_include(obj, indent)
    elif isinstance(obj, LineComment):
        return _format_linecomment(obj, indent)
    elif isinstance(obj, BlockComment):
        return _format_blockcomment(obj, indent)
    else:
        raise ValueError(f'cannot format object as TDL: {obj!r}')


def _format_term(term, indent):
    fmt = {
        TypeIdentifier: _format_id,
        String: _format_string,
        Regex: _format_regex,
        Coreference: _format_coref,
        AVM: _format_avm,
        _ImplicitAVM: _format_avm,
        ConsList: _format_conslist,
        DiffList: _format_difflist,
    }.get(term.__class__, None)

    if fmt is None:
        raise TDLError('not a valid term: {}'
                       .format(type(term).__name__))

    if term.docstring is not None:
        return '{}\n{}{}'.format(
            _format_docstring(term.docstring, indent),
            ' ' * indent,
            fmt(term, indent))
    else:
        return fmt(term, indent)


def _format_id(term, indent):
    return str(term)


def _format_string(term, indent):
    return f'"{term!s}"'


def _format_regex(term, indent):
    return f'^{term!s}$'


def _format_coref(term, indent):
    return f'#{term!s}'


def _format_avm(avm, indent):
    lines = []
    for feat, val in avm.features():
        val = _format_conjunction(val, indent + len(feat) + 3)
        if not val.startswith('\n'):
            feat += ' '
        lines.append(feat + val)
    if not lines:
        return '[ ]'
    else:
        return '[ {} ]'.format((',\n' + ' ' * (indent + 2)).join(lines))


def _format_conslist(cl, indent):
    values = [_format_conjunction(val, indent + 2)  # 2 = len('< ')
              for val in cl.values()]
    end = ''
    if not cl.terminated:
        if values:
            end = ', ...'
        else:
            values = ['...']
    elif cl._avm is not None and cl[cl._last_path] is not None:
        end = ' . ' + values[-1]
        values = values[:-1]

    if not values:  # only if no values and terminated
        return '< >'
    elif (len(values) <= _max_inline_list_items
          and sum(len(v) + 2 for v in values) + 2 + indent <= _line_width):
        return '< {} >'.format(', '.join(values) + end)
    else:
        i = ' ' * (indent + 2)  # 2 = len('< ')
        lines = [f'< {values[0]}']
        lines.extend(i + val for val in values[1:])
        return ',\n'.join(lines) + end + ' >'


def _format_difflist(dl, indent):
    values = [_format_conjunction(val, indent + 3)  # 3 == len('<! ')
              for val in dl.values()]
    if not values:
        return '<! !>'
    elif (len(values) <= _max_inline_list_items
          and sum(len(v) + 2 for v in values) + 4 + indent <= _line_width):
        return '<! {} !>'.format(', '.join(values))
    else:
        # i = ' ' * (indent + 3)  # 3 == len('<! ')
        return '<! {} !>'.format(
            (',\n' + ' ' * (indent + 3)).join(values))
        #     values[0])]
        # lines.extend(i + val for val in values[1:])
        # return ',\n'.join(lines) + ' !>'


def _format_conjunction(conj, indent):
    if isinstance(conj, Term):
        return _format_term(conj, indent)
    elif len(conj._terms) == 0:
        return ''
    else:
        tokens = []
        width = indent
        for term in conj._terms:
            tok = _format_term(term, width)
            flen = max(len(s) for s in tok.splitlines())
            width += flen + 3  # 3 == len(' & ')
            tokens.append(tok)
        lines = [tokens]  # all terms joined without newlines (for now)
        return (' &\n' + ' ' * indent).join(
            ' & '.join(line) for line in lines if line)


def _format_typedef(td, indent):
    i = ' ' * indent
    if hasattr(td, 'affix_type'):
        patterns = ' '.join(f'({a} {b})' for a, b in td.patterns)
        body = _format_typedef_body(td, indent, indent + 2)
        return '{}{} {}\n%{} {}\n  {}.'.format(
            i, td.identifier, td._operator, td.affix_type, patterns, body)
    else:
        body = _format_typedef_body(
            td, indent, indent + len(td.identifier) + 4)
        return '{}{} {} {}.'.format(i, td.identifier, td._operator, body)


def _format_typedef_body(td, indent, offset):
    parts = [[]]
    for term in td.conjunction.terms:
        if isinstance(term, AVM) and len(parts) == 1:
            parts.append([])
        parts[-1].append(term)

    if parts[0] == []:
        parts = [parts[1]]
    assert len(parts) <= 2
    if len(parts) == 1:
        formatted_conj = _format_conjunction(td.conjunction, offset)
    else:
        formatted_conj = '{} &\n{}{}'.format(
            _format_conjunction(Conjunction(parts[0]), offset),
            ' ' * (_base_indent + indent),
            _format_conjunction(Conjunction(parts[1]), _base_indent + indent))

    if td.docstring is not None:
        docstring = '\n  ' + _format_docstring(td.docstring, 2)
    else:
        docstring = ''

    return formatted_conj + docstring


def _format_docstring(doc, indent):
    if doc is None:
        return ''
    lines = textwrap.dedent(doc).splitlines()
    if lines:
        if lines[0].strip() == '':
            lines = lines[1:]
        if lines[-1].strip() == '':
            lines = lines[:-1]
    ind = ' ' * indent
    contents = _escape_docstring(
        '\n{0}{1}\n{0}'.format(ind, ('\n' + ind).join(lines)))
    return f'"""{contents}"""'


def _escape_docstring(s):
    cs = []
    cnt = 0
    lastindex = len(s) - 1
    for i, c in enumerate(s):
        if cnt == -1 or c not in '"\\':
            cnt = 0
        elif c == '"':
            cnt += 1
            if cnt == 3 or i == lastindex:
                cs.append('\\')
                cnt = 0
        elif c == '\\':
            cnt = -1
        cs.append(c)
    return ''.join(cs)


def _format_morphset(obj, indent):
    if isinstance(obj, LetterSet):
        mstype = 'letter-set'
    elif isinstance(obj, WildCard):
        mstype = 'wild-card'
    else:
        raise TypeError(f'not a valid morph-set class: {type(obj).__name__}')
    return '{}%({} ({} {}))'.format(
        ' ' * indent, mstype, obj.var, obj.characters
    )


def _format_environment(env, indent):
    status = ''
    if isinstance(env, TypeEnvironment):
        envtype = ':type'
    elif isinstance(env, InstanceEnvironment):
        envtype = ':instance'
        if env.status:
            status = ' :status ' + env.status

    contents = '\n'.join(format(obj, indent + 2) for obj in env.entries)
    if contents:
        contents += '\n'
    return '{0}:begin {1}{2}.\n{3}{0}:end {1}.'.format(
        ' ' * indent, envtype, status, contents)


def _format_include(fi, indent):
    return '{}:include "{}".'.format(' ' * indent, fi.value)


def _format_linecomment(obj, indent):
    return '{};{}'.format(' ' * indent, str(obj))


def _format_blockcomment(obj, indent):
    return '{}#|{}|#'.format(' ' * indent, str(obj))
