"""
Serialize DMRS objects into LaTeX code for visualization.
"""

from pathlib import Path

from delphin import predicate
from delphin import dmrs

__version__ = '1.0.0'

CODEC_INFO = {
    'representation': 'dmrs',
}

HEADER = """
\\documentclass{standalone}

\\usepackage{tikz-dependency}
\\usepackage{relsize}

%%%
%%% style for dmrs graph
%%%
\\depstyle{dmrs}{edge unit distance=1.5ex,
  label style={above, scale=.9, opacity=0, text opacity=1},
  baseline={([yshift=-0.7\\baselineskip]current bounding box.north)}}
%%% set text opacity=0 to hide text, opacity = 0 to hide box
\\depstyle{root}{edge unit distance=3ex, label style={opacity=1}}
\\depstyle{arg}{edge above}
\\depstyle{rstr}{edge below, dotted, label style={text opacity=1}}
\\depstyle{eq}{edge below, label style={text opacity=1}}
\\depstyle{icons}{edge below, dashed}
\\providecommand{\\named}{}
\\renewcommand{\\named}{named}

%%% styles for predicates and roles (from mrs.sty)
\\providecommand{\\spred}{}
\\renewcommand{\\spred}[1]{\\mbox{\\textsf{#1}}}
\\providecommand{\\srl}{}
\\renewcommand{\\srl}[1]{\\mbox{\\textsf{\\smaller #1}}}
%%%

\\begin{document}"""

JOINER = '\n'

FOOTER = """
\\end{document}
"""

# latex character escaping code copied from Xigt:
#   (https://github.com/xigt/xigt)

# order matters here
_LATEX_CHARMAP = [
    ('\\', '\\textbackslash'),
    ('&', '\\&'),
    ('%', '\\%'),
    ('$', '\\$'),
    ('#', '\\#'),
    ('_', '\\_'),
    ('{', '\\{'),
    ('}', '\\}'),
    ('~', '\\textasciitilde'),
    ('^', '\\textasciicircum'),
]


def _latex_escape(s):
    # consider a re sub with a function. e.g.
    # _character_unescapes = {
    #   '\\s': _field_delimiter,
    #   '\\n': '\n',
    #   '\\\\': '\\'}
    # _unescape_func = lambda m: _character_unescapes[m.group(0)]
    # _unescape_re = re.compile(r'(\\s|\\n|\\\\)')
    # _unescape_re.sub(_unescape_func, string, flags=re.UNICODE)
    for c, r in _LATEX_CHARMAP:
        s = s.replace(c, r)
    return s


def dump(ds, destination, properties=True, lnk=True,
         indent=False, encoding='utf-8'):
    """
    Serialize DMRS objects for LaTeX + tikz-dependency and write to a file.

    Args:
        ds: an iterator of DMRS objects to serialize
        destination: filename or file object where data will be written
        properties: (unused)
        lnk: (unused)
        indent: (unused)
        encoding (str): if *destination* is a filename, write to the
            file with the given encoding; otherwise it is ignored
    """
    text = dumps(ds, properties=properties, lnk=lnk, indent=indent)
    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        destination = Path(destination).expanduser()
        with destination.open('w', encoding=encoding) as fh:
            print(text, file=fh)


def dumps(ds, properties=True, lnk=True, indent=True):
    """
    Serialize DMRS objects for LaTeX + tikz-dependency.

    Args:
        ds: an iterator of DMRS objects to serialize
        properties: (unused)
        lnk: (unused)
        indent (bool, int): (unused)
    Returns:
        LaTeX code for rendering the DMRSs in *ds*.
    """
    parts = [HEADER]
    for d in ds:
        parts.append(encode(d, properties=properties, lnk=lnk, indent=indent))
    parts.append(FOOTER)
    return JOINER.join(parts)


def encode(d, properties=True, lnk=True, indent=True):
    """
    Serialize a single DMRS object *d* for LaTeX + tikz-dependency.

    Args:
        d: DMRS object to serialize
        properties: (unused)
        lnk: (unused)
        indent (bool, int): (unused)
    Returns:
        LaTeX code for rendering the DMRS *d*.
    """
    lines = []
    lines.append("\\begin{dependency}[dmrs]")
    ns = d.nodes
    # predicates
    lines.append("  \\begin{deptext}[column sep=10pt]")
    for i, n in enumerate(ns):
        sep = "\\&" if (i < len(ns) - 1) else "\\\\"
        pred = _latex_escape(predicate.normalize(n.predicate))
        pred = "\\named{}" if pred == 'named' else pred
        if n.carg is not None:
            pred += "\\smaller ({})".format(n.carg.strip('"'))
        lines.append("    \\spred{{{}}} {}     % node {}".format(
            pred, sep, i+1))
    lines.append("  \\end{deptext}")
    nodeidx = {n.id: i for i, n in enumerate(ns, 1)}

    # links
    if d.top is not None:
        lines.append('  \\deproot[root]{{{}}}{{{}}}'
                     .format(nodeidx[d.top], '\\srl{TOP}'))
        # _latex_escape('/' + link.post)

    for link in d.links:
        lines.append('  \\depedge[{}]{{{}}}{{{}}}{{\\srl{{{}}}}}'.format(
            _label_edge(link),
            nodeidx[link.start],
            nodeidx[link.end],
            _latex_escape(_link_label(link))
        ))
    # placeholder for icons
    lines.append('%  \\depedge[icons]{f}{t}{FOCUS}')
    lines.append('\\end{dependency}\n')
    return '\n'.join(lines)


def _link_label(link):
    return '{}/{}'.format(link.role or '', link.post)


def _label_edge(link):
    if link.post == dmrs.H_POST and link.role == dmrs.RESTRICTION_ROLE:
        return 'rstr'
    elif link.post == dmrs.EQ_POST:
        return 'eq'
    else:
        return 'arg'
