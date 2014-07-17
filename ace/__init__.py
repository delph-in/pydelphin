#!/usr/bin/env python -*- coding: utf-8 -*-

import os

ace_download_url = "http://sweaglesw.org/linguistics/ace/download/"
ace_bleeding_edge =  "ace-0.9.17-x86-64.tar.gz"
ace_version =  ace_bleeding_edge.partition('-x86-64')[0]

erg_bleeding_edge = "erg-1212-x86-64-0.9.17.dat.bz2"
erg_version = erg_bleeding_edge.rpartition('.')[0]

home_path = os.path.expanduser("~") + "/"
ace_cmd = "~/aceparser/" + ace_version + "/ace -g ~/aceparser/" + erg_version + " " 
ace_path = home_path + "aceparser/"

##erg_lextdl = home_path + '/delphin/erg/lexicon.tdl'

def install():
    if not os.path.exists(ace_path):
        os.makedirs(ace_path)

    # Downloads ACE and ERG.
    if not os.path.exists(home_path + ace_bleeding_edge):
        download_ace = " ".join(["wget", "-P", home_path, 
                         ace_download_url+ace_bleeding_edge])
        os.system(download_ace)
    if not os.path.exists(home_path + erg_bleeding_edge):
        download_erg = " ".join(["wget", "-P", home_path, 
                        ace_download_url+erg_bleeding_edge ])
        os.system(download_erg)

    # Exact ACE and ERG.
    if not os.path.exists(ace_path+ace_version+"/ace"):
        extract_ace = " ".join(["tar", "-zxvf", home_path+ace_bleeding_edge, 
                        "-C", ace_path])
        os.system(extract_ace)
    if not os.path.exists(ace_path+erg_version):
        extract_erg = " ".join(["bzip2", "-dc", home_path+erg_bleeding_edge, 
                                ">", ace_path+erg_version])
        os.system(extract_erg)
        
def parse(sent, onlyMRS=False, parameters="", bestparse=False):
    if onlyMRS == True:
            parameters+=" -T "
    pipe_sent_in = "echo " +sent+" | "
    cmd = pipe_sent_in + ace_cmd +" 2> silence"
    ace_output = [p.strip() for p in os.popen(cmd) 
                  if p.strip() != ""]
    if bestparse:
        return ace_output[1]
    else:
        return ace_output