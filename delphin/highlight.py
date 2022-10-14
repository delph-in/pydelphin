
"""
Pygments-based highlighting lexers for DELPH-IN formats.
"""

import re

from pygments.lexer import RegexLexer, include, bygroups
from pygments.style import Style
from pygments.token import (
    Text, Number, String,
    Keyword, Name, Operator, Punctuation,
    Comment, Error
)

# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401

_tdl_break_characters = re.escape(r'<>!=:.#&,[];$()^/')


class TDLLexer(RegexLexer):
    """
    A Pygments-based Lexer for Typed Description Language.
    """
    name = 'TDL'
    aliases = ['tdl']
    filenames = ['*.tdl']

    tokens = {
        'root': [
            (r'\s+', Text),
            include('comment'),
            (r'(\S+?)(\s*)(:[=<+])', bygroups(Name.Class, Text, Operator),
             'typedef'),
            (r'(%)(\s*\(\s*)(letter-set|wild-card)',
             bygroups(Operator, Punctuation, Name.Builtin),
             ('letterset', 'letterset')),  # need to pop twice
            (r':begin', Name.Builtin, 'macro')
        ],
        'comment': [
            (r';.*?$', Comment.Singleline),
            (r'#\|', Comment.Multiline, 'multilinecomment')
        ],
        'multilinecomment': [
            (r'[^#|]', Comment.Multiline),
            (r'#\|', Comment.Multiline, '#push'),
            (r'\|#', Comment.Multiline, '#pop'),
            (r'[#|]', Comment.Multiline)
        ],
        'typedef': [
            (r'\s+', Text),
            (r'\.', Punctuation, '#pop'),
            # probably ok to reuse letterset for %suffix and %prefix
            (r'(%prefix|%suffix)', Name.Builtin, 'letterset'),
            include('conjunction')
        ],
        'conjunction': [
            (r'\s+', Text),
            (r'&', Operator),
            (r'"[^"\\]*(?:\\.[^"\\]*)*"', String.Doc),
            include('term'),
            (r'', Text, '#pop')
        ],
        'term': [
            include('comment'),
            (r'\[', Punctuation, 'avm'),
            (r'<!', Punctuation, 'difflist'),
            (r'<', Punctuation, 'conslist'),
            (r'#[^\s{}]+'.format(_tdl_break_characters), Name.Label),
            include('strings'),
            (r'\*top\*', Keyword.Constant),
            (r'\.\.\.', Name),
            (r'[^\s{}]+'.format(_tdl_break_characters), Name),
            (r'', Text, '#pop')
        ],
        'avm': [
            include('comment'),
            (r'\s+', Text),
            (r'\]', Punctuation, '#pop'),
            (r',', Punctuation),
            (r'((?:[^\s{0}]+)(?:\s*\.\s*[^\s{0}]+)*)'
             .format(_tdl_break_characters), Name.Attribute, 'conjunction')
        ],
        'conslist': [
            (r'>', Punctuation, '#pop'),
            (r',|\.', Punctuation),
            include('conjunction')
        ],
        'difflist': [
            (r'!>', Punctuation, '#pop'),
            (r',|\.', Punctuation),
            include('conjunction')
        ],
        'strings': [
            (r'"""([^"\\]|\\.|"(?!")|""(?!"))*"""', String.Doc),
            (r'"[^"\\]*(?:\\.[^"\\]*)*"', String.Double),
            (r"'[^ \\]*(?:\\.[^ \\]*)*", String.Single),
            (r"\^[^ \\]*(?:\\.[^ \\]*)*\$", String.Regex)
        ],
        'letterset': [
            (r'\(', Punctuation, '#push'),
            (r'\)|\n', Punctuation, '#pop'),
            (r'!\w', Name.Variable),
            (r'\s+', Text),
            (r'\*', Name.Constant),
            (r'.', String.Char)
        ],
        'macro': [
            (r'\s+', Text),
            include('comment'),
            (r'(:end.*?)(\.)', bygroups(Name.Builtin, Punctuation), '#pop'),
            (r'(:begin.*?)(\.)', bygroups(Name.Builtin, Punctuation), '#push'),
            (r':[-\w]+', Name.Builtin),
            include('strings'),
            (r'[-\w]+', Name),
            (r'\.', Punctuation)
        ]
    }


class MRSStyle(Style):
    styles = {
        Text:           '',
        Punctuation:    '',
        Name.Attribute: '#757575',
        Name.Builtin:   'bold',
        Name.Variable:  '#00B2CA bold',
        Name.Label:     '#E8BE5D bold',
        Name.Function:  '#EF476F bold',
        Name.Other:     '#7E56D6 bold',
        Operator.Word:  '',
        String:         '',
        String.Single:  '',
        String.Double:  '',
        String.Symbol:  '#06D6A0 bold',
        String.Other:   '#05C095',
        Number:         '#757575',
        Error:          '#FF0000 underline',
    }


class SimpleMRSLexer(RegexLexer):
    """
    A Pygments-based Lexer for the SimpleMRS serialization format.
    """
    name = 'SimpleMRS'
    aliases = ['mrs']
    filenames = ['*.mrs']

    tokens = {
        'root': [
            (r'\s+', Text),
            (r'\[', Punctuation, 'mrs')
        ],
        'mrs': [
            (r'\s+', Text),
            include('strings'),
            include('vars'),
            (r'\]', Punctuation, '#pop'),
            (r'<', Number, 'lnk'),
            (r'(TOP|LTOP|INDEX)(\s*)(:)',
             bygroups(Name.Builtin, Text, Punctuation)),
            (r'(RELS|HCONS|ICONS)(\s*)(:)(\s*)(<)',
             bygroups(Name.Builtin, Text, Punctuation, Text, Punctuation),
             'list'),
        ],
        'strings': [
            (r'"[^"\\]*(?:\\.[^"\\]*)*"', String.Double),
            (r"'[^ \\]*(?:\\.[^ \\]*)*", String.Single),
        ],
        'vars': [
            (r'(?:h|handle)\d+', Name.Label),
            (r'(?:e|event)\d+', Name.Function, 'var'),
            (r'(?:x|ref-ind)\d+', Name.Variable, 'var'),
            (r'(?:i|individual|p|non_event|u|semarg)\d+', Name.Other, 'var'),
        ],
        'var': [
            (r'\s+', Text),
            (r'\[', Punctuation, 'proplist'),
            (r'', Text, '#pop')
        ],
        'proplist': [
            (r'\s+', Text),
            (r'([^:\s]+)(\s*)(:)(\s*)([^\s]+)',
             bygroups(Name.Attribute, Text, Punctuation, Text, Text)),
            (r'e|event', Name.Function),
            (r'x|ref-ind', Name.Variable),
            (r'\w+', Name.Other),
            (r'\]', Punctuation, '#pop'),
        ],
        'lnk': [
            (r'\s+', Text),
            (r'>', Number, '#pop'),
            (r'\d+[:#]\d+|@\d+|\d+(?:\s+\d+)*', Number),
        ],
        'list': [
            (r'\s+', Text),
            (r'>', Punctuation, '#pop'),
            (r'\[', Punctuation, ('ep', 'pred')),
            include('vars'),
            (r'qeq|outscopes|lheq|[^\s]+', Operator.Word),
        ],
        'ep': [
            (r'\s+', Text),
            (r'<', Number, 'lnk'),
            (r'\]', Punctuation, '#pop'),
            include('strings'),
            (r'(LBL)(\s*)(:)',
             bygroups(Name.Namespace, Text, Punctuation)),
            (r'(ARG0)(\s*)(:)',
             bygroups(Name.Class, Text, Punctuation)),
            (r'(CARG)(\s*)(:)',
             bygroups(Name.Constant, Text, Punctuation)),
            (r'([^:\s]+)(\s*)(:)',
             bygroups(Name.Tag, Text, Punctuation)),
            include('vars')
        ],
        'pred': [
            (r'\s+', Text),
            (r'"[^"_\\]*(?:\\.[^"\\]*)*"', String.Symbol, '#pop'),
            (r"'[^ _\\]*(?:\\.[^ \\]*?)*", String.Symbol, '#pop'),
            (r'([^ \\]*(?:\\.[^ \\]*)*)(<[-0-9:#@ ]*>)',
             bygroups(String.Symbol, Number),
             '#pop'),
            (r'([^ \\]*(?:\\.[^ \\]*)*)\s', String.Symbol, '#pop'),
        ]
    }

    def get_tokens_unprocessed(self, text):
        for idx, tok, val in RegexLexer.get_tokens_unprocessed(self, text):
            if tok is String.Symbol and ('_q_' in val or val.endswith('_q')):
                yield idx, String.Other, val
            else:
                yield idx, tok, val
