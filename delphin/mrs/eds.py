
from itertools import count

def dump(fh, ms, single=False, pretty_print=True, color=False, **kwargs):
    print(dumps(ms,
                single=single,
                pretty_print=pretty_print,
                color=color,
                **kwargs),
          file=fh)

def dumps(ms, single=False, pretty_print=True, color=False, **kwargs):
    if single:
        ms = [ms]
    return '\n'.join(
        serialize(ms, pretty_print=pretty_print, color=color, **kwargs)
    )

eds = '{{{index}{delim}{ed_list}}}'
ed =  '{membership}{id}:{pred}{lnk}{carg}[{dep_list}]{delim}'
carg = '({constant})'
dep = '{argname} {value}'

def serialize(ms, pretty_print=True, color=False, **kwargs):
    q_ids = ('_{}'.format(i) for i in count(start=1))
    delim = '\n'
    connected = ' '
    disconnected = '|'
    if not pretty_print:
        delim = ' '
        connected = ''
    for m in ms:
        yield eds.format(
            index=str(m.index) + ':' if m.index is not None else '',
            delim=delim,
            ed_list=''.join(
                ed.format(
                    membership=connected,  # if m.is_connected(ep.nodeid)?
                    id=ep.cv if not ep.is_quantifier() else next(q_ids),
                    pred=ep.pred.short_form(),
                    lnk=str(ep.lnk),
                    carg=carg.format(constant=ep.carg) if ep.carg else '',
                    dep_list=(
                        ', '.join(
                            dep.format(argname=a.argname, value=a.value)
                            for a in m.get_outbound_args(ep.nodeid,
                                                         allow_unbound=False)
                        ) if not ep.is_quantifier() else
                        dep.format(argname='BV', value=ep.cv)
                    ),
                    delim=delim
                )
                for ep in m.eps
            )
        )
