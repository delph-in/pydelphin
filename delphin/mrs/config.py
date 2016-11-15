# encoding: UTF-8

# constants used throughout the mrs library
# In the future, these should probably move to a proper settings module

LTOP_NODEID    = 0
FIRST_NODEID   = 10000 # the nodeid assigned to the first node
# sortal values
UNKNOWNSORT    = 'u' # when nothing is known about the sort
HANDLESORT     = 'h' # for scopal relations
# useful pos values
QUANTIFIER_POS = 'q' # for quantifier preds
# MRS strings
IVARG_ROLE     = 'ARG0'
CONSTARG_ROLE  = 'CARG'
# DMRS strings
RSTR_ROLE      = 'RSTR' # DMRS establishes that quantifiers have a RSTR link
EQ_POST        = 'EQ'
HEQ_POST       = 'HEQ'
NEQ_POST       = 'NEQ'
H_POST         = 'H'
NIL_POST       = 'NIL'
CVARSORT       = 'cvarsort'
BARE_EQ_ROLE   = 'MOD'
