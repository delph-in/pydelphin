
"""
Dependency Minimal Recursion Semantics ([DMRS]_)

.. [DMRS] Copestake, Ann. Slacker Semantics: Why superficiality,
  dependency and avoidance of commitment can be the right way to go.
  In Proceedings of the 12th Conference of the European Chapter of
  the Association for Computational Linguistics, pages 1–9.
  Association for Computational Linguistics, 2009.
"""

# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401
from delphin.dmrs._dmrs import (
    BARE_EQ_ROLE,
    CVARSORT,
    DMRS,
    EQ_POST,
    FIRST_NODE_ID,
    H_POST,
    HEQ_POST,
    NEQ_POST,
    RESTRICTION_ROLE,
    Link,
    Node,
)
from delphin.dmrs._exceptions import (
    DMRSError,
    DMRSSyntaxError,
    DMRSWarning,
)
from delphin.dmrs._operations import from_mrs

__all__ = [
    'FIRST_NODE_ID',
    'RESTRICTION_ROLE',
    'BARE_EQ_ROLE',
    'EQ_POST',
    'HEQ_POST',
    'NEQ_POST',
    'H_POST',
    'CVARSORT',
    'DMRS',
    'Node',
    'Link',
    'from_mrs',
    'DMRSError',
    'DMRSSyntaxError',
    'DMRSWarning',
]
