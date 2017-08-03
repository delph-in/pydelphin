
# Every jaded manager of some employee fond of pranks quits.
# every ( some ( udef ( prank, employee ^ fond ), jaded ^ manager ), quit )
# every ( udef ( prank, some ( employee ^ fond, jaded ^ manager ) ), quit )
# some ( udef ( prank, employee ^ fond ), every ( jaded ^ manager, quit ) )
# udef ( prank, every ( some ( employee ^ fond, jaded ^ manager ), quit ) )
# udef ( prank, some ( employee ^ fond, every ( jaded ^ manager, quit ) ) )

# every :
# jaded : =manager
# manager : employee
# some :
# employee : --
# fond : =employee , prank
# udef :
# prank :
# quit : manager

# The dog whose tail wagged barked.
# the ( def_explicit ( tail, dog ^ poss ^ wag ), bark )
# def_explicit ( tail, the ( dog ^ poss ^ wag, bark ) )

# the :
# dog :
# poss : tail, =dog
# def_explicit :
# tail :
# wag : tail
# bark : dog

# Kim believed Sandy could fail.
# proper_q ( Kim, believe ( could ( proper_q ( Sandy, fail ) ) ) )
# proper_q ( Kim, believe ( proper_q ( Sandy, could ( fail ) ) ) )
# proper_q ( Kim, proper_q ( Sandy, believe ( could ( fail ) ) ) )
# proper_q ( Sandy, proper_q ( Kim, believe ( could ( fail ) ) ) )

# proper_q :
# Kim :
# believe : Kim, $(could)
# proper_q :
# Sandy :
# could : $(fail)
# fail : Sandy

# Very nearly every dog barked.
# very(e6, e5) ^ nearly(e5, u4) ^ every(x3, dog(x3), bark(e2, x3))
# {
#   "top": [
#     {"pred": "very", "ARG0": "e6", "ARG1": "e5"},
#     {"pred": "nearly", "ARG0": "e5", "ARG1": "u4"},
#     {"pred": "every", "BV": "x3",
#      "RSTR": [
#       {"pred": "dog", "ARG0": "x3"},
#      ],
#      "BODY": [
#       {"pred": "bark", "ARG0": "e2", "ARG1": "x3"}
#      ]
#     }
#   ]
# }

def scopes(x, method='exhaustive'):
    nonqs = dict((nid, x.ep(nid)) for nid in x.nodeids(quantifier=False))
    ivs = dict((ep.intrinsic_variable, ep.nodeid) for ep in nonqs.values())
    qs = dict((nid, x.ep(nid)) for nid in x.nodeids(quantifier=True))
    lbls = set(x.labels())
    lblsets = {lbl: x.labelset(lbl) for lbl in lbls}
    print(lblsets)
    dsets = {}
    for lbl in lbls:
        dset = set()
        for nid in lblsets[lbl]:
            for arg, val in x.outgoing_args(nid).items():
                if val in ivs:
                    dset.add(ivs[val])
                elif val in lbls:
                    pass
        dsets[lbl] = dset
    print(dsets)



# def exhaustive_scopes(x):
#     pass

# def make_scoped_mrs(x):
#     topvars = []
#     intermediate_scopes = []
#     rels = x.eps()
#     hcons = x.hcons()
#     qs = x.eps(x.nodeids(quantifier=True))
#     implicit_existentials = []
#     free_vars = [v for v in implicit_existentials if varsort(v) != 'x']
#     if free_vars:
#         raise Exception()
#     else:
#         for res in create_scoped_structures(...):
#             if not res_struct_other_rels(res):
#                 yield res_struct_bindings(res)

# def create_scoped_structures(top, bvs, bindings, rels, scoping_handles, pending_qeq, scoped_p, scoping_rels):
#     # if not scope limit, do the following
#     # return cached results, if available, else
#     return fresh_create_scoped_structures(top, bvs, bindings, rels, scoping_handles, pending_qeq, scoped_p, scoping_rels)

# def fresh_create_scoped_structures(top, bvs, bindings, rels, scoping_handles, pending_qeq, scoped_p, scoping_rels):
#     pass
