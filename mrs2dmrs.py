from delphin.mrs import simplemrs, dmrx
import sys

m = simplemrs.load(open(sys.argv[1]))
print(simplemrs.encode(m, pretty_print=True))
print()
#print(m.find_head_ep())
#print()
print(dmrx.encode(m, pretty_print='lkb'))
