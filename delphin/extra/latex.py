
from delphin.mrs.components import nodes, links
from delphin.mrs.xmrs import Xmrs

# latex character escaping code copied from Xigt:
#   (https://github.com/xigt/xigt)

# order matters here
LATEX_CHARMAP = [
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

def latex_escape(s):
    # consider a re sub with a function. e.g.
    # _character_unescapes = {'\\s': _field_delimiter, '\\n': '\n', '\\\\':     '\\'}
    # _unescape_func = lambda m: _character_unescapes[m.group(0)]
    # _unescape_re = re.compile(r'(\\s|\\n|\\\\)')
    # _unescape_re.sub(_unescape_func, string, re.UNICODE)
    for c, r in LATEX_CHARMAP:
        s = s.replace(c, r)
    return s

def dmrs_tikz_dependency(xs):
    if isinstance(xs, Xmrs):
        xs = [xs]
    lines = [
        '\\documentclass{standalone}',
        '\\usepackage{tikz-dependency}',
        '\\begin{document}'
    ]
    for x in xs:
        lines.append('\\begin{dependency}[label style={font=\\footnotesize}]')
        ns = nodes(x)
        ls = links(x)
        predlist = [latex_escape(n.pred.short_form()) for n in ns]
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
                        'TOP'  # latex_escape('/' + link.post)
                    )
                )
            else:
                lines.append('  \\depedge{{{}}}{{{}}}{{{}}}'.format(
                    nodeidx[link.start],
                    nodeidx[link.end],
                    latex_escape('{}/{}'.format(link.rargname, link.post))
                ))
        lines.append('\\end{dependency}')
    lines.append('\\end{document}')
    return '\n'.join(lines)
