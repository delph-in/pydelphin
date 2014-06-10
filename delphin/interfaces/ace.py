
"""ACE interface for DOE commands"""

import logging
from subprocess import Popen, PIPE, STDOUT
from .util import decode_stagfile, encode_stagfile
from delphin.iterfaces import _do

def do(cmd):
    # validate cmd here (e.g. that it has a 'grammar' key, correct 'task', etc)
    task = cmd['task']
    grammar = cmd['grammar']
    cmdargs = cmd['arguments'] + ['-g', grammar]
    if task == 'parse':
        process_output = parse_results
    elif task == 'transfer':
        process_output = transfer_results
    elif task == 'generate':
        process_output = generation_results
    else:
        logging.error('Task "{}" is unsupported by the ACE interface.'
                      .format(task))
        return
    cmdargs = map(lambda a: a.format(**cmd['variables']), cmdargs)
    _do()

def process(cmd, infile, outfile, config):
    c = config['commands'][cmd]
    ct = config['commandtypes'][c['type']]
    cmdargs = map(lambda a: a.format(**config['variables']), c['arguments'])
    # try...except this
    task = ct['task']
    key = ct['input_key']
    if task == 'parse':
        parse_output = parse_results
    elif task == 'generate':
        parse_output = generation_results
    elif task == 'transfer':
        parse_output = transfer_results
    else:
        pass #log this
    outstream = open(outfile, 'w')
    with Popen(cmdargs, stdin=PIPE, stdout=PIPE, stderr=STDOUT,
               universal_newlines=True) as ace:
        for item_id, provenance, data in decode_stagfile(open(infile,'r')):
            indata = data.get(key)
            if indata is None: continue
            ace.stdin.write(indata + '\n')
            ace.stdin.flush()
            for result_id, result in parse_output(ace.stdout):
                print(encode_stagfile(
                        item_id,
                        provenance + ['{}:{}'.format(cmd, result_id)],
                        result),
                      file=outstream)
    outstream.close()


def parse_results(instream):
    item = {}
    status = None
    counter = 0
    line = instream.readline()
    while line:
        if line.startswith('SENT:'):
            pass
        elif line.startswith('SKIP:'):
            pass
        elif line.startswith('WARNING:'):
            pass
        elif line.startswith('ERROR:'):
            pass
        elif line.startswith('NOTE:'):
            status = 'NOTE'
        elif line.strip() == '':
            if status == 'BLANK':
                break
            else:
                status = 'BLANK'
        else:
            mrs, dtree = line.split(' ; ')
            yield (counter, {'mrs': mrs.strip(), 'derivation': dtree.strip()})
            counter += 1
        line = instream.readline()

def generation_results(instream):
    item = {}
    status = None
    counter = 0
    line = instream.readline()
    while line:
        if line.startswith('NOTE:'):
            break
        else:
            yield (counter, {'sentence': line.strip()})
            counter += 1
        line = instream.readline()

def format_input(data, field):
    return data.get(field, '')
