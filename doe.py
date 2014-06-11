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
#from delphin.codecs import itsdb
#import delphin.interfaces
#from delphin.utils import load_config

_rcfilename = '.pydelphinrc'

def main(args):
    config = load_config(args)
    doecfg = config['doe']
    if not validate(args, doecfg):
        sys.exit('Exiting.')

    if args.list:
        list_commands(doecfg)
        sys.exit()

    prepare_output_directory(config)
    in_profile = itsdb.load_profile()
    for command in args.commands:
        out_profile = 
        cmd = make_command(command, doecfg)
        interface = get_interface(cmd['interface'])
        interface.do(cmd)

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
        args.config = os.path.join(args.output_directory, _rcfilename)
    else:
        sys.exit('No config file found. Exiting.')

    logging.debug('Loading the config file found at {}'.format(args.config))
    config = json.loads(strip_json_comments(open(args.config,'r')),
                        object_pairs_hook=OrderedDict)
    doecfg = config['doe']

    # override the loaded values with those from the command-line
    if 'variables' not in doecfg:
        doecfg['variables'] = {}
    if args.source_grammar:
        doecfg['variables']['source_grammar'] = args.source_grammar
    if args.transfer_grammar:
        doecfg['variables']['transfer_grammar'] = args.transfer_grammar
    if args.target_grammar:
        doecfg['variables']['target_grammar'] = args.target_grammar
    if args.grammar:
        doecfg['variables']['grammar'] = args.grammar
    if args.output_directory:
        doecfg['output_directory'] = args.output_directory
    if args.input_profile:
        doecfg['input_profile'] = args.input_profile
    if args.verbosity:
        doecfg['verbosity'] = args.verbosity

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
        if len(args.commands) == 0:
            logging.error('At least one command is required.')
            valid = False
        if args.output_directory is None:
            logging.error('An --output-directory argument is required.')
            valid = False
        if args.input_profile is None:
            logging.error('An --input-profile argument is required.')
            valid = False
    return valid 


def list_commands(config):
    print('Commands:')
    for c, cmd in config['commands'].items():
        print('  {}: {}'.format(c, cmd.get('description')))

def prepare_output_directory(config):
    #if not config.get('output_directory'):
    #    config['output_directory'] = os.getcwd()
    doecfg = config['doe']
    outdir = doecfg['output_directory']
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
    rcpath = os.path.join(doecfg['output_directory'], _rcfilename)
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser('pyDelphin Operating Environment')
    # the --list option is a specific kind of help that uses the config.
    # When it is not used, --outdir and a command are required, but we
    # can't use argparse to state the requirement (validate later)
    parser.add_argument('-l', '--list', action='store_true',
        help='list the commands allowed by the configuration')
    parser.add_argument('-v', '--verbose', action='count', dest='verbosity',
        default=2, help='increase the verbosity (can be repeated: -vvv)')
    parser.add_argument('-q', '--quiet', action='store_const', const=0,
        dest='verbosity', help='set verbosity to the quietest level')
    parser.add_argument('-o', '--output-directory', metavar='DIR',
        help='the output directory for all commands')
    parser.add_argument('-i', '--input-profile', metavar='PATH',
        help='the [incr tsdb()] profile to use as input for the first '
             'command')
    parser.add_argument('-c', '--config', metavar='PATH',
        help='the configuration file describing possible commands')
    parser.add_argument('-s', '--source-grammar', metavar='PATH')
    parser.add_argument('-x', '--transfer-grammar', metavar='PATH')
    parser.add_argument('-t', '--target-grammar', metavar='PATH')
    parser.add_argument('-g', '--grammar', metavar='PATH')
    parser.add_argument('commands', nargs='*')

    args = parser.parse_args()
    logging.basicConfig(level=50-(args.verbosity*10))

    main(args)
