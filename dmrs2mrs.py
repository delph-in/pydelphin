from delphin.mrs import simplemrs, dmrx
import sys

m = dmrx.decode(open(sys.argv[1]))
print(dmrx.encode(m, pretty_print='lkb'))
print()
print(m.find_head_ep())
print()
print(simplemrs.encode(m))