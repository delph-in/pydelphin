
import re
from pygments.lexer import RegexLexer, include, bygroups
from pygments.token import (
    Text, Keyword, Name, String, Operator, Punctuation, Comment
)

tdl_break_characters = re.escape(r'<>!=:.#&,[];$()^/')

class TdlLexer(RegexLexer):
    name = 'TDL'
    aliases = ['tdl']
    filenames = ['*.tdl']

    tokens = {
        'root': [
            (r'\s+', Text),
            include('comment'),
            (r'(\S+?)(\s*)(:[=<+])', bygroups(Name.Class, Text, Operator),
             'typedef'),
            (r'(%)(\s*\(\s*)(letter-set)',
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
            (r'#[^\s{}]+'.format(tdl_break_characters), Name.Label),
            include('strings'),
            (r'\*top\*', Keyword.Constant),
            (r'\.\.\.', Name),
            (r'[^\s{}]+'.format(tdl_break_characters), Name),
            (r'', Text, '#pop')
        ],
        'avm': [
            include('comment'),
            (r'\s+', Text),
            (r'\]', Punctuation, '#pop'),
            (r',', Punctuation),
            (r'((?:[^\s{0}]+)(?:\s*\.\s*[^\s{0}]+)*)'
             .format(tdl_break_characters), Name.Attribute, 'conjunction')
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