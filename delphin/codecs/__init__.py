# codecs have been moved to their respective modules (e.g. delphin.mrs)
# so import them here for (temporary) backward compatibility.

import warnings
warnings.warn(
    'The delphin.codecs modules have been deprecated. Look for them '
    'under their respective packages (e.g. simplemrs is at '
    'delphin.mrs.simplemrs).',
    DeprecationWarning
)

from delphin.mrs import simplemrs, mrx, dmrx
