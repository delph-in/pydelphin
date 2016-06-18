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
    # _unescape_re.sub(_unescape_func, string, re.UNICODE)
    for c, r in _LATEX_CHARMAP:
        s = s.replace(c, r)
    return s

def dmrs_tikz_dependency(xs):
    """
    Return a LaTeX document with each Xmrs in *xs* rendered as DMRSs.

    DMRSs use the tikz-dependency package for visualization.
    """
    def link_label(link):
        return '{}/{}'.format(link.rargname or '', link.post)

    def label_side(link):
        if ((link.post == H_POST and link.rargname == RSTR_ROLE)
                or link.post == EQ_POST):
            return 'edge below'
        return 'edge above'

    if isinstance(xs, Xmrs):
        xs = [xs]

    slots = defaultdict(set)  # from/(+-)to; + for above, - for below
    lines = [
        '\\documentclass{standalone}',
        '\\usepackage{tikz-dependency}',
        '\\begin{document}'
    ]
    for x in xs:
        lines.append(
            '\\begin{dependency}['
            'text only label,'
            'label style={above,font=\\footnotesize},'
            'edge unit distance=2ex'
            ']'
        )
        ns = nodes(x)
        ls = links(x)
        predlist = [_latex_escape(n.pred.short_form()) for n in ns]
        lines.extend([
            '  \\begin{deptext}[column sep=10pt]',
            '    {} \\\\'.format(' \\& '.join(predlist)),
            '  \\end{deptext}'
        ])
        nodeidx = {n.nodeid: i+1 for i, n in enumerate(ns)}
        for link in links(x):
            if link.start == 0:
                lines.append(
                    '  \\deproot[edge unit distance=2ex]{{{}}}{{{}}}'.format(
                        nodeidx[link.end],
                        'TOP'  # _latex_escape('/' + link.post)
                    )
                )
            else:
                side = label_side(link)
                opts = [side]
                slot = link.end * -1 if side.endswith('below') else link.end
                if slot in slots[link.start]:
                    opts.append('edge unit distance=4ex')
                slots[link.start].add(slot)
                lines.append('  \\depedge[{}]{{{}}}{{{}}}{{{}}}'.format(
                    ','.join(opts),
                    nodeidx[link.start],
                    nodeidx[link.end],
                    _latex_escape(link_label(link))
                ))
        lines.append('\\end{dependency}')
    lines.append('\\end{document}')
    return '\n'.join(lines)
