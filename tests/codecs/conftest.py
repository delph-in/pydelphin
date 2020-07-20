
import pytest

from delphin import mrs
from delphin.lnk import Lnk


@pytest.fixture
def nearly_all_dogs_bark_mrs():
    return mrs.MRS(
        top='h0',
        index='e2',
        rels=[
            mrs.EP('_nearly_x_deg', 'h4',
                   args={'ARG0': 'e5', 'ARG1': 'u6'},
                   lnk=Lnk('<0:6>')),
            mrs.EP('_all_q', 'h4',
                   args={'ARG0': 'x3', 'RSTR': 'h7', 'BODY': 'h8'},
                   lnk=Lnk('<7:10>')),
            mrs.EP('_dog_n_1', 'h9',
                   args={'ARG0': 'x3'},
                   lnk=Lnk('<11:15>')),
            mrs.EP('_bark_v_1', 'h1',
                   args={'ARG0': 'e2', 'ARG1': 'x3'},
                   lnk=Lnk('<16:20>')),
        ],
        hcons=[mrs.HCons.qeq('h0', 'h1'), mrs.HCons.qeq('h7', 'h9')],
        icons=[],
        variables={
            'e2': {'SF': 'prop', 'TENSE': 'pres', 'MOOD': 'indicative',
                   'PROG': '-', 'PERF': '-'},
            'e5': {'SF': 'prop', 'TENSE': 'untensed', 'MOOD': 'indicative',
                   'PROG': '-', 'PERF': '-'},
            'x3': {'PERS': '3', 'NUM': 'pl', 'IND': '+', 'PT': 'pt'},
        },
        lnk=Lnk('<0:21>'),
        surface='Nearly all dogs bark.',
        identifier='10'
    )
