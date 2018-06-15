
"""
Interface modules for external data providers.

PyDelphin interfaces manage the communication between PyDelphin and
external DELPH-IN data providers. A data provider could be a local
process, such as the `ACE <http://sweaglesw.org/linguistics/ace/>`_
parser/generator, or a remote service, such as the `DELPH-IN RESTful
web server <http://moin.delph-in.net/ErgApi>`_. The interfaces send
requests to the providers, then receive and interpret the response. The
interfaces may also detect and deserialize supported DELPH-IN formats.

"""
