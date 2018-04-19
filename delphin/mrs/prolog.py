
"""
Serialization functions for the Prolog format.
"""


# Author: Michael Wayne Goodman <goodmami@uw.edu>

from __future__ import print_function


def dump(fh, ms, single=False, pretty_print=False, **kwargs):
    """
    Serialize [Xmrs] objects to the Prolog representation and write
    to a file

    Args:
        fh: filename or file object
        ms: an iterator of [Xmrs] objects to serialize (unless the
            *single* option is `True`)
        single: if `True`, treat *ms* as a single [Xmrs] object
            instead of as an iterator
        pretty_print: if `True`, the output is formatted to be easier
            to read
    Returns:
      None
    """
    print(dumps(ms,
                single=single,
                pretty_print=pretty_print,
                **kwargs),
          file=fh)


def dumps(ms, single=False, pretty_print=False, **kwargs):
    """
    Serialize an [Xmrs] object to the Prolog representation

    Args:
        ms: an iterator of [Xmrs] objects to serialize (unless the
            *single* option is `True`)
        single: if `True`, treat *ms* as a single [Xmrs] object instead
            of as an iterator
        pretty_print: if `True`, the output is formatted to be easier to
            read
    Returns:
        the Prolog string representation of a corpus of [Xmrs]
    """
    if single:
        ms = [ms]
    return serialize(ms, pretty_print=pretty_print, **kwargs)

dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)



def serialize(ms, pretty_print=False, **kwargs):
    """Serialize an MRS structure into Prolog."""
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

