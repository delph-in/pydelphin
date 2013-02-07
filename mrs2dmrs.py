from delphin.mrs import simplemrs, dmrx
import sys

m = simplemrs.load(open(sys.argv[1]))
print(dmrx.encode_dmrs(m, pretty_print='lkb'))
