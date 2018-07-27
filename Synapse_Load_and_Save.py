#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue May 22 10:47:54 2018

@author: cl321
"""

import synapseclient
import argparse
import os
import datetime
import pandas as pd
import sys
import shutil

"""get user input"""
parser = argparse.ArgumentParser()
parser.add_argument('username')
parser.add_argument('password')
parser.add_argument('dir_project')
parser.add_argument('synapse_ids')
parser.add_argument('R_variable_name', nargs='?', default=None)

args = parser.parse_args()

username = args.username
password = args.password
dir_project = args.dir_project
synapse_ids = args.synapse_ids
R_variable_name = args.R_variable_name

if R_variable_name != None:
    R_variable_name = R_variable_name.split(',')
synapse_id_list = synapse_ids.split(',')
    
"""make connect to synapse, set directories"""
syn=synapseclient.Synapse()
syn.login(username, password)

dir_c_script = os.getcwd()
dir_log = dir_c_script + '/' + os.path.basename(dir_c_script)+'_SynapseLog'
time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
tempdir = dir_project + 'temp_local_synapse_files'+time
os.mkdir(tempdir)

def get_synapse_info(synapse_id, download):
    file_info = {}
    for index, syn_id in enumerate(synapse_id_list):
        entity = syn.get(syn_id, downloadFile=download, downloadLocation=tempdir,
                         ifcollision= 'overwrite.local')
        file_info[index]={}
        try:
            file_info[index]['file_name'] = entity.name
        except AttributeError:
            pass
        if R_variable_name==None:
            file_info[index]['R_variable_name'] = os.path.splitext(entity.name)[0]
        else:
            file_info[index]['R_variable_name'] = R_variable_name[index]
        try:
            file_info[index]['id'] = entity.id
            file_info[index]['url']='http://synapse.sagebase.org/#Synapse:'+entity.id
        except AttributeError:
            pass
        try:
            file_info[index]['description'] = entity.description
        except AttributeError:
            pass
        try:
            file_info[index]['url'] = entity.url
        except AttributeError:
            pass
        try:
            file_info[index]['version_number'] = entity.versionNumber
        except AttributeError:
            pass
        try:
            file_info[index]['versions_label'] = entity.versionLabel
        except AttributeError:
            pass
        try:
            file_info[index]['DateTime_modified'] = entity.modifiedOn
        except AttributeError:
            pass
    file_info_final = pd.DataFrame(file_info).T
    return file_info_final

"""get info of files copied in for user to check"""
check_file_info = get_synapse_info(synapse_id_list, False)

print 'to be loaded '+ ','.join(check_file_info['file_name'].tolist())
print '==========================================================='
print "please check 'file_info' before continuing loading process"

"""download files from Synapse"""
file_info_tosave = get_synapse_info(synapse_id_list, True)

syn.logout()

"""write logfile"""
if not os.path.exists(dir_log):
    os.mkdir(dir_log)

currentscript_insert = os.path.splitext(os.path.basename(sys.argv[0]))[0]
[logfilename1, logfilename2] = datetime.datetime.now().strftime('%Y%m%d_%H%M%S').split('_')
logfile_name = dir_log+'/FilesUsed_'+logfilename1+'_'+currentscript_insert+'_'+logfilename2+'_GMT.csv'
file_info_tosave.to_csv(logfile_name, index=False)
    
"""load data into R"""
files = file_info_tosave['file_name'].tolist()
if len(files)==0:    
    print 'something went wrong'

filedict = {}
for index, afile in enumerate(files):
    varname = file_info_tosave.iloc[index]['R_variable_name']
    afile = pd.read_csv(tempdir+'/'+file_info_tosave.iloc[index]['file_name'],
                        index_col=0)
    filedict[varname] = afile

shutil.rmtree(tempdir)    
