"""
Generate LaTeX snippets for rendering DELPH-IN data.
"""

from collections import defaultdict

from delphin.mrs.components import nodes, links
from delphin.mrs.config import (
    RSTR_ROLE, EQ_POST, H_POST
)

from delphin.mrs.xmrs import Xmrs

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
    # _character_unescapes = {'\\s': _field_delimiter, '\\n': '\n', '\\\\':     '\\'}
    # _unescape_func = lambda m: _character_unescapes[m.group(0)]
    # _unescape_re = re.compile(r'(\\s|\\n|\\\\)')
    # _unescape_re.sub(_unescape_func, string, flags=re.UNICODE)
    for c, r in _LATEX_CHARMAP:
        s = s.replace(c, r)
    return s

def dmrs_tikz_dependency(xs, **kwargs):
    """
    Return a LaTeX document with each Xmrs in *xs* rendered as DMRSs.

    DMRSs use the `tikz-dependency` package for visualization.
    """
    def link_label(link):
        return '{}/{}'.format(link.rargname or '', link.post)

    def label_edge(link):
        if link.post == H_POST and link.rargname == RSTR_ROLE:
            return 'rstr'
        elif link.post == EQ_POST:
            return 'eq'
        else:
            return 'arg'

    if isinstance(xs, Xmrs):
        xs = [xs]

    lines = """\\documentclass{standalone}

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

\\begin{document}""".split("\n")
    
    for ix, x in enumerate(xs):
        lines.append("%%%\n%%% {}\n%%%".format(ix+1)) 
        lines.append("\\begin{dependency}[dmrs]")
        ns = nodes(x)
        ### predicates
        lines.append("  \\begin{deptext}[column sep=10pt]")
        for i, n in enumerate(ns):
            sep = "\\&"  if  (i < len(ns) - 1) else  "\\\\"
            pred = _latex_escape(n.pred.short_form())
            pred = "\\named{}" if pred == 'named' else pred
            if n.carg is not None:
                print(n.carg.strip('"'))
                pred += "\\smaller ({})".format(n.carg.strip('"'))
            lines.append("    \\spred{{{}}} {}     % node {}".format(
                pred, sep, i+1))
        lines.append("  \\end{deptext}")
        nodeidx = {n.nodeid: i+1 for i, n in enumerate(ns)}
        ### links
        for link in links(x):
            if link.start == 0:
                lines.append(
                    '  \\deproot[root]{{{}}}{{{}}}'.format(
                        nodeidx[link.end],
                        '\\srl{TOP}'  # _latex_escape('/' + link.post)
                    )
                )
            else:
                lines.append('  \\depedge[{}]{{{}}}{{{}}}{{\\srl{{{}}}}}'.format(
                    label_edge(link),
                    nodeidx[link.start],
                    nodeidx[link.end],
                    _latex_escape(link_label(link))
                ))
        ### placeholder for icons
        lines.append('%  \\depedge[icons]{f}{t}{FOCUS}')
        lines.append('\\end{dependency}\n')
    lines.append('\\end{document}')
    return '\n'.join(lines)
