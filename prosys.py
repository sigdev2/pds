#!/usr/bin/env python
# -*- coding: utf-8 -*-

r''' Copyright 2018, SigDev

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License. '''

import os
import shutil
import six
from zipfile import ZipFile
from optparse import OptionParser

try:
    # Python 2.6-2.7 
    from urllib2 import urlopen
except ImportError:
    # Python 3
    from urllib.request import urlopen

# utils

def file_get_contents(filename):
    if not(os.path.exists(filename)):
        return False
    with open(filename, r'r') as f:
        return f.read()

def file_write_contents(filename, content, mode = r'w'):
    with open(filename, mode) as f:
        f.write(content)

def structToProj(src, target):
    for root, dirs, files in os.walk(src):
        for d in dirs:
            path = target + root.replace(src, r'') + os.sep + d
            if not(os.path.exists(path)):
                os.makedirs(path)
        for f in files:
            path = target + root.replace(src, r'') + os.sep + f
            if not(os.path.exists(path)):
                shutil.copyfile(root + os.sep + f, path)

# consts

SERVER_URL = r'https://raw.githubusercontent.com/sigdev2/prosys/master/'
TPL_VERSION_FILE = r'TEMPLATES_VERSION'
TPL_ARCHIVE = r'templates.zip'
TPL_FOLDER = r'templates/'

CUR_TPL_VERSION_FILE = r'./' + TPL_VERSION_FILE
CUR_TPL_ARCHIVE = r'./' + TPL_ARCHIVE
CUR_TPL_FOLDER = r'./' + TPL_FOLDER

# parse args

parser = OptionParser(usage=r'usage: %prog [options] module1 module2')
parser.add_option(r'-o', r'--out', dest=r'proj', help=r'create or check project in DIRNAME', metavar=r'DIRNAME')
parser.add_option(r'-l', r'--list', action=r'store_true', dest=r'showlist', help=r'show modules list', default=False)

(opts, args) = parser.parse_args()

# check updates templates

server_tpl_version = 0
for line in urlopen(SERVER_URL + TPL_VERSION_FILE):
    server_tpl_version = int(line)

current_tpl_version = file_get_contents(CUR_TPL_VERSION_FILE)
if current_tpl_version == False or not(os.path.exists(CUR_TPL_FOLDER)):
    current_tpl_version = 0
else:
    current_tpl_version = int(current_tpl_version)

if server_tpl_version == 0 and not(os.path.exists(CUR_TPL_FOLDER)):
    six.print_(r'ERROR: Current and remote versions of templates is broken. Can not restore template version!')
    exit()

if server_tpl_version > current_tpl_version:
    six.print_(r'Update templates ...')
    try:
        file_write_contents(CUR_TPL_VERSION_FILE, str(server_tpl_version))
        filedata = urlopen(SERVER_URL + TPL_ARCHIVE)
        datatowrite = filedata.read()
        file_write_contents(CUR_TPL_ARCHIVE, datatowrite, r'bw')
        if os.path.exists(CUR_TPL_FOLDER):
            shutil.rmtree(CUR_TPL_FOLDER)
        with ZipFile(CUR_TPL_ARCHIVE, r'r') as zipObj:
            zipObj.extractall()
        six.print_(r'Templates update successfully!')
    except Exception:
        six.print_(r'ERROR: Can not update templates! Try skip update ...')
        if not(os.path.exists(CUR_TPL_FOLDER)):
            six.print_(r'ERROR: Templates is not exists!')
            exit()

# list of templates

if opts.showlist:
    six.print_('\nList of available templates: \n')
    six.print_('    Name:\tVersion:\n')
    for dirname in os.listdir(CUR_TPL_FOLDER):
        six.print_(r'    ' + dirname.replace(r'_ver=', '\t'))
    six.print_('\n')
    exit()

# applay proj path

if not opts.proj:
    six.print_(r'ERROR: Specify the path to the project!')
    exit()

projPath = os.path.abspath(opts.proj)
if not(projPath[-1] == os.sep):
    projPath += os.sep

if not(os.path.exists(projPath)):
    os.makedirs(projPath)
    six.print_(r'Projcet directory created !')

# integrate modules

for dirname in os.listdir(CUR_TPL_FOLDER):
    name = dirname.split(r'_ver=')[0]
    if name in args:
        six.print_(r'use ' + name)
        structToProj(CUR_TPL_FOLDER + dirname, projPath)

six.print_(r'Sucess!')