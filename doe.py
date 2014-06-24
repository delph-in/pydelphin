#!/usr/bin/env python3

import sys
import os
import argparse
import logging
import json
import re
from collections import OrderedDict
from copy import deepcopy
from importlib import import_module
from delphin import itsdb, mrs

_rcfilename = '.pydelphinrc'


def main(args):
    config = load_config(args)
    doecfg = config['doe']
    if not validate(args, doecfg):
        sys.exit('Exiting.')

    if args.list:
        list_commands(doecfg)
        sys.exit()

    in_profile = prepare_input_profile(doecfg)
    prepare_output_profile(config)

    if args.select:
        print(args.select)
        table, cols = get_data_specifier(args.select)
        print('\n'.join(in_profile.select(table, cols, mode='row')))

    #for command in args.commands:
    #    out_profile = None
    #    cmd = make_command(command, doecfg)
    #    interface = get_interface(cmd['interface'])
    #    interface.do(cmd)


def load_config(args):
    """
    Load a configuration file. Configurations may be loaded from 3 places. In
    order of precedence:
       1. the argument of the -c (--config) option
       2. a .stagrc file in the current directory
       3. a .stagrc file in the $HOME directory
    Only one of the above may be loaded. Additionally, configuration options
    given explicitly at the command line override any loaded values.
    """
    if args.config is not None:
        if not os.path.exists(args.config):
            sys.exit('Config file not found: {}'.format(args.config))
        # will be loaded below
    elif os.path.exists(os.path.join(os.getcwd(), _rcfilename)):
        args.config = os.path.join(os.getcwd(), _rcfilename)
    elif os.path.exists(os.path.join(os.environ['HOME'], _rcfilename)):
        args.config = os.path.join(args.output_profile, _rcfilename)
    else:
        sys.exit('No config file found. Exiting.')

    logging.debug('Loading the config file found at {}'.format(args.config))
    config = json.loads(strip_json_comments(open(args.config,'r')),
                        object_pairs_hook=OrderedDict)
    cfg = config['doe']

    # override the loaded values with those from the command-line
    cfg.update({
        'verbosity': args.verbosity,
        'input_profile': args.input_profile or cfg.get('input_profile'),
        'output_profile': args.output_profile or cfg.get('output_profile'),
        'select': args.select or cfg.get('select'),
        'apply': args.apply or cfg.get('apply', []),
        'filter': args.filter or cfg.get('filter', []),
    })
    # these overrides need some nesting, so do them separate
    if 'variables' not in cfg:
        cfg['variables'] = {}
    if args.source_grammar:
        cfg['variables']['source_grammar'] = args.source_grammar
    if args.transfer_grammar:
        cfg['variables']['transfer_grammar'] = args.transfer_grammar
    if args.target_grammar:
        cfg['variables']['target_grammar'] = args.target_grammar
    if args.grammar:
        cfg['variables']['grammar'] = args.grammar

    return config

json_single_comment_re = re.compile(r'^\s*//')
json_start_comment_re = re.compile(r'^\s*/\*')
json_end_comment_re = re.compile(r'\*/\s*$')
def strip_json_comments(fh):
    in_comment = False
    lines = []
    for line in fh:
        if in_comment:
            if json_end_comment_re.search(line):
                in_comment = False
        elif json_start_comment_re.match(line):
            in_comment = True
        elif not json_single_comment_re.match(line):
            lines.append(line)
    return ''.join(lines)


def validate(args, doecfg):
    """ Validate arguments not caught by argparse. """
    valid = True
    if not args.list:
        #if len(args.commands) == 0:
        #    logging.error('At least one command is required.')
        #    valid = False
        if args.output_profile is None:
            logging.error('An --output-profile argument is required.')
            valid = False
        if args.input_profile is None:
            logging.error('An --input-profile argument is required.')
            valid = False
    return valid


def list_commands(config):
    print('Commands:')
    for c, cmd in config['commands'].items():
        print('  {}: {}'.format(c, cmd.get('description')))


def prepare_input_profile(cfg):
    prof = itsdb.TsdbProfile(cfg['input_profile'])
    print(cfg.get('filter'))
    for spr, f in cfg.get('filter', []):
        table, cols = get_data_specifier(spr)
        f = make_lambda_function(f)
        prof.add_filter(table, cols, f)
    for spr, f in cfg.get('apply', []):
        table, cols = get_data_specifier(spr)
        f = make_lambda_function(f)
        prof.add_applicator(table, cols, f)
    return prof


def prepare_output_profile(config):
    #if not config.get('output_directory'):
    #    config['output_directory'] = os.getcwd()
    doecfg = config['doe']
    outdir = doecfg['output_profile']
    try:
        os.makedirs(outdir, exist_ok=True)
    except PermissionError:
        logging.critical('Permission denied to create output directory: {}'
                         .format(outdir))
        sys.exit(1)
    if not os.access(outdir, mode=os.R_OK|os.W_OK):
        logging.critical('Cannot write to output directory: {}'
                         .format(outdir))
        sys.exit(1)
    # copy configuration for documentation
    # TODO: allow for multiple configs in same directory (e.g. (PID).rcfile)
    rcpath = os.path.join(doecfg['output_profile'], _rcfilename)
    if not os.path.exists(rcpath):
        json.dump(config, open(rcpath, 'w'), indent=2)
    else:
        logging.warning('Config file path already exists: {}'.format(rcpath))

def make_command(command, doecfg):
    # make a copy so changes for this command do not affect later ones
    cmd = deepcopy(doecfg['commands'][command])
    cpu_name = cmd['cpu']
    cpu = doecfg['cpus'][cpu_name]
    task_name = cmd['task']
    task = cpu['tasks'][task_name]
    cmd['executable'] = cpu['executable']
    cmd['arguments'] = cpu.get('arguments', []) + task.get('arguments', [])
    cmd['interface'] = cpu.get('interface', 'generic')
    # if grammar is given explicitly, use it, otherwise use
    # task-specific grammar (already in the command)
    if doecfg.get('grammar'):
        cmd['grammar'] = doecfg['grammar']
    return cmd


def get_interface(interface_name):
    return import_module('{}.{}'.format('delphin.interfaces', interface_name))


data_specifier_re = re.compile(r'(?P<table>[^:]+)(:(?P<cols>.+))?$')
def get_data_specifier(string):
    """
    Return a tuple (table, col) for some [incr tsdb()] data specifier.
    For example:

      item              -> ('item', None)
      item:i-input      -> ('item', ['i-input'])
      item:i-input@i-wf -> ('item', ['i-input', 'i-wf'])
      (otherwise)       -> (None, None)
    """
    match = data_specifier_re.match(string)
    if match is None:
        return (None, None)
    table = match.group('table').strip()
    cols = match.group('cols')
    if cols is not None:
        cols = list(map(str.strip, cols.split('@')))
    return (table, cols)


def make_lambda_function(function):
    return eval('lambda row, x:{}'.format(function))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''
DATA SPECIFIERS
  The --select, --apply, and --filter options take as a first argument
  a string to specify the table and, if desired or necessary, the column
  from a [incr tsdb()] profile to draw data from. These take the form:
    TABLE[:COL[@COL..]]
  For example, this selects an entire row from the `item` table:
    item
  while this selects the `i-id` and `i-input` columns for each row:
    item:i-id@i-input
  For --select and --filter, the COL specifiers are optional. For
  --apply, at least one COL is required.

FILTER/APPLY EXPRESSIONS
  The --filter and --apply options take as a second argument a small
  Python expression to be evaluated. This expression is turned into a
  lambda expression like this:
      f = lambda row, x: EXPR
  Thus, EXPR can use `row`, which is the contents of the entire row as a
  Python dictionary, and `x` is the value of the current column (if COLs
  are specified, otherwise it is None). The type of `x` is a string for
  --apply, and it will be a string for --filter unless an --apply
  operation has recast it. For example, these are equivalent and select
  all rows in `item` where the `i-id` field has an integer value less
  than 10:
    --filter item "int(row['i-id']) < 10"
    --filter item:i-id "int(x) < 10"
    --apply item:i-id "int(x)" --filter item:i-id "x < 10"
  Note, however, that the last one with the --apply operation differs in
  that the value of `item:i-id` remains an `int` after the filtering.
        '''
    )
    add = parser.add_argument
    add('-c', '--config',
        metavar='PATH',
        help='The configuration file describing possible commands.')
    # the --list option is a specific kind of help that uses the config.
    # When it is not used, --outdir and a command are required, but we
    # can't use argparse to state the requirement (validate later)
    add('-l', '--list',
        action='store_true',
        help='List the commands allowed by the configuration.')
    add('-v', '--verbose',
        action='count', dest='verbosity', default=2,
        help='Increase the verbosity (can be repeated: -vvv).')
    add('-q', '--quiet',
        action='store_const', const=0, dest='verbosity',
        help='Set verbosity to the quietest level.')
    add('-i', '--input-profile',
        metavar='PATH',
        help='The [incr tsdb()] profile to use as input.')
    add('-o', '--output-profile',
        metavar='PATH',
        help='The [incr tsdb()] profile to output.')
    add('-s', '--select',
        metavar='TBL[:COL[@COL..]]',
        help='Print the contents of each row in TBL. If COLs are specified, '
             'only print contents of these columns. See also the section '
             'about DATA SPECIFIERS. e.g. '
             '--select item:i-input@i-wf')
    add('-a', '--apply',
        nargs=2, metavar=('TBL:COL[@COL..]', 'EXPR'), action='append',
        help='Apply EXPR to the contents of COL for each COL for each row '
             'in TBL. See also the section about DATA SPECIFIERS and '
             'FILTER/APPLY EXPRESSIONS. e.g. '
             '--apply result:mrs "mrs.convert(x, \'mrx\', \'dmrx\')"')
    add('-f', '--filter',
        nargs=2, metavar=('TBL[:COL[@COL..]]', 'EXPR'), action='append',
        help='Ignore rows from TBL where EXPR returns a non-true value for '
             'the row. If COLs are specified, EXPR is tested for every COL '
             'on each row. See also the section about DATA SPECIFIERS and '
             'FILTER/APPLY EXPRESSIONS. e.g. '
             '--filter item "int(row[\'i-length\']) < 5"')
    add('-S', '--source-grammar', metavar='PATH')
    add('-T', '--target-grammar', metavar='PATH')
    add('-X', '--transfer-grammar', metavar='PATH')
    add('-G', '--grammar', metavar='PATH')
    add('commands', nargs='*')

    args = parser.parse_args()
    logging.basicConfig(level=50-(args.verbosity*10))

    main(args)
