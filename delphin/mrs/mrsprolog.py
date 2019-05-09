
"""
Serialization functions for the Prolog format.

Example:
    >>> from delphin.interfaces import rest
    >>> from delphin.mrs import mrsprolog
    >>> response = rest.parse('The dog sleeps soundly.', params={'mrs':'json'})
    >>> print(mrsprolog.dumps([response.result(0).mrs()], indent=True))
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

from delphin.sembase import role_priority
from delphin.mrs import CONSTANT_ROLE


def dump(ms, destination, properties=True, lnk=True,
         indent=False, encoding='utf-8'):
    """
    Serialize MRS objects to the Prolog representation and write to a file.

    Args:
        ms: an iterator of MRS objects to serialize
        destination: filename or file object where data will be written
        properties: if `True`, encode variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
        encoding (str): if *destination* is a filename, write to the
            file with the given encoding; otherwise it is ignored
    """
    text = dumps(ms, properties=properties, lnk=lnk, indent=indent)
    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        with open(destination, 'w', encoding=encoding) as fh:
            print(text, file=fh)


def dumps(ms, properties=True, lnk=True, indent=False):
    """
    Serialize MRS objects to the Prolog representation

    Args:
        ms: an iterator of MRS objects to serialize
        properties: if `True`, encode variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        the Prolog string representation of a corpus of MRSs
    """
    return _encode(ms, properties=properties, lnk=lnk, indent=indent)


def encode(m, properties=True, lnk=True, indent=False):
    """
    Serialize a MRS object to a Prolog string.

    Args:
        m: an MRS object
        properties (bool): if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        a Prolog-serialization of the MRS object
    """
    return _encode_mrs(m, properties, lnk, indent)


def _encode(ms, properties, lnk, indent):
    if indent is not None and indent is not False:
        delim = '\n'
    else:
        delim = ' '
    return delim.join(_encode_mrs(m, properties, lnk, indent) for m in ms)


def _encode_mrs(m, properties, lnk, indent):
    pl = 'psoa({topvars},{_}[{rels}],{_}hcons([{hcons}]){icons})'
    plvc = '{reln}({left},{right})'
    # pre-compute the various indent levels
    if indent is None or indent is False:
        _, __, ___, ____ = '', ',', '', ','
    else:
        if indent is True:
            indent = 2
        _ = '\n' + (' ' * indent)
        __ = ',' + _ + (' ' * len('['))
        ___ = _ + (' ' * len('[rel('))
        ____ = __ + (' ' * len('rel(['))

    topvars = [str(m.top)]
    if m.index is not None:
        topvars.append(str(m.index))
    rels = [_encode_rel(rel, ___, ____) for rel in m.rels]
    icons = ''
    if m.icons:
        icons = ',{_}icons([{ics}])'.format(
            _=_,
            ics=','.join(
                plvc.format(reln=ic.relation, left=ic.left, right=ic.right)
                for ic in m.icons
            )
        )
    return pl.format(
        topvars=','.join(topvars),
        rels=__.join(rels),
        hcons=','.join(
            plvc.format(reln=hc.relation, left=hc.hi, right=hc.lo)
            for hc in m.hcons
        ),
        icons=icons,
        _=_,
        ___=___
    )


def _encode_rel(ep, ___, ____):
    args = []
    plav = "attrval('{}',{})"
    for role in sorted(ep.args, key=role_priority):
        val = ep.args[role]
        if role == CONSTANT_ROLE:
            val = "'{}'".format(val)
        args.append(plav.format(role, val))
    return "rel('{pred}',{lbl},{___}[{attrvals}])".format(
        pred=ep.predicate,
        lbl=ep.label,
        ___=___,
        attrvals=____.join(args))
