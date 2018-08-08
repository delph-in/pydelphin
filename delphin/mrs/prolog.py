
"""
Serialization functions for the Prolog format.

Example:
    >>> from delphin.interfaces import rest
    >>> from delphin.mrs import prolog
    >>> response = rest.parse('The dog sleeps soundly.', params={'mrs':'json'})
    >>> print(prolog.dumps([response.result(0).mrs()], pretty_print=True))
    psoa(h1,e3,
    [rel('_the_q',h4,
        [attrval('ARG0',x6),
            attrval('RSTR',h7),
            attrval('BODY',h5)]),
    rel('_dog_n_1',h8,
        [attrval('ARG0',x6)]),
    rel('_sleep_v_1',h2,
        [attrval('ARG0',e3),
            attrval('ARG1',x6)]),
    rel('_sound_a_1',h2,
        [attrval('ARG0',e9),
            attrval('ARG1',e3)])],
    hcons([qeq(h1,h2),qeq(h7,h8)]))
"""


# Author: Michael Wayne Goodman <goodmami@uw.edu>

from __future__ import print_function


def dump(destination, ms, single=False, pretty_print=False, **kwargs):
    """
    Serialize Xmrs objects to the Prolog representation and write to a file.

    Args:
        destination: filename or file object where data will be written
        ms: an iterator of Xmrs objects to serialize (unless the
            *single* option is `True`)
        single: if `True`, treat *ms* as a single Xmrs object
            instead of as an iterator
        pretty_print: if `True`, add newlines and indentation
    """
    text = dumps(ms,
                 single=single,
                 pretty_print=pretty_print,
                 **kwargs)

    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        with open(destination, 'w') as fh:
            print(text, file=fh)


def dumps(ms, single=False, pretty_print=False, **kwargs):
    """
    Serialize an Xmrs object to the Prolog representation

    Args:
        ms: an iterator of Xmrs objects to serialize (unless the
            *single* option is `True`)
        single: if `True`, treat *ms* as a single Xmrs object instead
            of as an iterator
        pretty_print: if `True`, add newlines and indentation
    Returns:
        the Prolog string representation of a corpus of Xmrs
    """
    if single:
        ms = [ms]
    return serialize(ms, pretty_print=pretty_print, **kwargs)

dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)



def serialize(ms, pretty_print=False, **kwargs):
    # structures
    pl = 'psoa({topvars},{_}[{rels}],{_}hcons([{hcons}]){icons})'
    plep = "rel('{pred}',{lbl},{___}[{attrvals}])"
    plav = "attrval('{attr}',{val})"
    plvc = '{reln}({left},{right})'
    # various indent levels
    delim = '\n' if pretty_print else ' '
    _ = '\n  ' if pretty_print else ''  # lizst, hcons, icons
    __ = ',\n   ' if pretty_print else ','  # rels
    ___ = '\n       ' if pretty_print else ''  # attrlist
    ____ = ',\n        ' if pretty_print else ','  # attrval
    outputs = []
    for m in ms:
        mvars = set(m.variables())
        topvars = [str(m.top)]
        if m.index is not None: topvars.append(str(m.index))
        icons = ''
        if m.icons():
            icons = ',{_}icons([{ics}])'.format(
                _=_,
                ics=','.join(
                    plvc.format(reln=ic.relation, left=ic.left, right=ic.right)
                    for ic in m.icons()
                )
            )
        output = pl.format(
            topvars=','.join(topvars),
            rels=__.join(
                plep.format(
                    pred=ep.pred.string,
                    lbl=ep.label,
                    ___=___,
                    attrvals=____.join(
                        plav.format(
                            attr=rarg,
                            val=val if val in mvars else "'{}'".format(val)
                        )
                        for rarg, val in ep.args.items()
                    )
                )
                for ep in m.eps()
            ),
            hcons=','.join(
                plvc.format(reln=hc.relation, left=hc.hi, right=hc.lo)
                for hc in m.hcons()
            ),
            icons=icons,
            _=_, ___=___
        )
        outputs.append(output)
    return delim.join(outputs)
