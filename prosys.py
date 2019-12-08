#!/usr/bin/env python
# -*- coding: utf-8 -*-

r''' Copyright 2020, SigDev

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
import mimetypes
from zipfile import ZipFile
from optparse import OptionParser

try:
    # Python 2.6-2.7
    from urllib2 import urlopen
    import string

    def translate(s, t):
        return s.translate(string.maketrans(r'', r''), t)
except ImportError:
    # Python 3
    from urllib.request import urlopen

    def translate(s, t):
        return s.translate(t)

# utils


def printProgressBar(message, total, pos,
                     decimals=1, length=100, fill=r'█', printEnd='\r'):
    value = 100 * (pos / float(total))
    percent = (r'{0:.' + str(decimals) + r'f}').format(value)
    filledLength = int(length * pos // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    six.print_('\r %s |%s| %s%%' % (message, bar, percent), end=printEnd)
    if pos >= total:
        six.print_()


def downloadProgress(file, bytes_red, total_size):
    printProgressBar(r'Download ' + file, total_size, bytes_red)


def chunkedDownload(file, response, chunk_size=8192):
    total_size = response.getheader(r'Content-Length').strip()
    total_size = int(total_size)
    bytes_red = 0
    data = None
    while 1:
        chunk = response.read(chunk_size)
        if not chunk:
            break
        if data is None:
            data = chunk
        else:
            data += chunk
        bytes_red += len(chunk)
        downloadProgress(file, bytes_red, total_size)
    return data


def is_text_file(filename):
    if not(os.path.exists(filename)):
        return False

    mime_type = mimetypes.guess_type(filename)[0]
    if not(mime_type is None):
        return mime_type.startswith(r'text')

    s = open(filename).read(512)
    text_characters = r''.join(map(chr, range(32, 127))) + '\n\r\t\b'
    if not s:
        return True
    if '\0' in s:
        return False
    t = translate(s, text_characters)
    return float(len(t))/float(len(s)) >= 0.70


def file_get_contents(filename):
    if not(os.path.exists(filename)):
        return False
    with open(filename, r'r') as f:
        return f.read()


def file_write_contents(filename, content, mode=r'w'):
    with open(filename, mode) as f:
        f.write(content)


def structToProj(src, target, macros):
    for root, dirs, files in os.walk(src):
        for d in dirs:
            path = target + root.replace(src, r'') + os.sep + d
            if not(os.path.exists(path)):
                os.makedirs(path)
        for f in files:
            path = target + root.replace(src, r'') + os.sep + f
            if not(os.path.exists(path)):
                shutil.copyfile(root + os.sep + f, path)
            if macros:
                if is_text_file(path):
                    c = file_get_contents(path)
                    for macro in macros:
                        c = c.replace(macro, macros[macro])
                    file_write_contents(path, c)

# consts


SERVER_URL = r'https://raw.githubusercontent.com/sigdev2/prosys/master/'
TPL_VERSION_FILE = r'TEMPLATES_VERSION'
TPL_ARCHIVE = r'templates.zip'
TPL_FOLDER = r'templates/'

CUR_TPL_VERSION_FILE = r'./' + TPL_VERSION_FILE
CUR_TPL_ARCHIVE = r'./' + TPL_ARCHIVE
CUR_TPL_FOLDER = r'./' + TPL_FOLDER

SRC_FOLDER_NAME = r'src'

MACROSES = [r'%%=PROJ_NAME%%', r'%%=PROJ_PATH%%']

if __name__ == r'__main__':

    # parse args

    parser = OptionParser(usage=r'usage: %prog [options] module1 module2')
    parser.add_option(r'-o', r'--out',
                      dest=r'proj',
                      help=r'create or check project in DIRNAME',
                      metavar=r'DIRNAME')
    parser.add_option(r'-l', r'--list',
                      action=r'store_true',
                      dest=r'showlist',
                      help=r'show modules list',
                      default=False)
    parser.add_option(r'-m', r'--macroses',
                      action=r'store_true',
                      dest=r'showmacroses',
                      help=r'show list or macroses to replace in files',
                      default=False)
    parser.add_option(r'-r', r'--replace',
                      action=r'store_true',
                      dest=r'replace',
                      help=r'replace macroses in copyed template files',
                      default=False)
    parser.add_option(r'-s', r'--src',
                      action=r'store_true',
                      dest=r'move',
                      help=r'move proj folder content to src folder',
                      default=False)

    (opts, args) = parser.parse_args()

    # list of macroses

    if opts.showmacroses:
        six.print_('\nList of macroses to replace in templates: \n')
        for m in MACROSES:
            six.print_(m)
        six.print_('\n')
        os._exit(1)

    # check updates templates

    server_tpl_version = 0
    res = urlopen(SERVER_URL + TPL_VERSION_FILE)
    server_tpl_version = int(chunkedDownload(TPL_VERSION_FILE, res))

    current_tpl_version = file_get_contents(CUR_TPL_VERSION_FILE)
    if current_tpl_version is False or not(os.path.exists(CUR_TPL_FOLDER)):
        current_tpl_version = 0
    else:
        current_tpl_version = int(current_tpl_version)

    if server_tpl_version == 0 and not(os.path.exists(CUR_TPL_FOLDER)):
        six.print_(r'ERROR: Current and remote versions of templates ' +
                   r'is broken. Can not restore template version!')
        os._exit(1)

    updated = False
    if server_tpl_version > current_tpl_version:
        six.print_(r'Update templates ...')
        try:
            file_write_contents(CUR_TPL_VERSION_FILE, str(server_tpl_version))
            res = urlopen(SERVER_URL + TPL_ARCHIVE)
            datatowrite = chunkedDownload(TPL_ARCHIVE, res)
            file_write_contents(CUR_TPL_ARCHIVE, datatowrite, r'bw')
            if os.path.exists(CUR_TPL_FOLDER):
                shutil.rmtree(CUR_TPL_FOLDER)
            with ZipFile(CUR_TPL_ARCHIVE, r'r') as zipObj:
                zipObj.extractall()
            six.print_(r'Templates update successfully!')
            updated = True
        except Exception:
            six.print_(r'ERROR: Can not update templates! Try skip update ...')
            if not(os.path.exists(CUR_TPL_FOLDER)):
                six.print_(r'ERROR: Templates is not exists!')
                os._exit(1)

    # list of templates

    if opts.showlist or updated:
        six.print_('\nList of available templates: \n')
        six.print_('    Name:\tVersion:\n')
        for dirname in os.listdir(CUR_TPL_FOLDER):
            six.print_(r'    ' + dirname.replace(r'_ver=', '\t'))
        six.print_('\n')
        if opts.showlist:
            os._exit(1)

    # applay proj path

    if not opts.proj:
        six.print_(r'ERROR: Specify the path to the project!')
        os._exit(1)

    projPath = os.path.abspath(opts.proj)
    if not(projPath[-1] == os.sep):
        projPath += os.sep

    if not(os.path.exists(projPath)):
        os.makedirs(projPath)
        six.print_(r'Projcet directory created !')
    else:
        if opts.move:
            c = os.listdir(projPath)
            if len(c) > 0:
                src_folder = projPath + SRC_FOLDER_NAME
                if not(os.path.exists(src_folder)):
                    os.makedirs(src_folder)
                for f in c:
                    if not (f == SRC_FOLDER_NAME):
                        shutil.move(projPath + f, src_folder)

    # collect macros

    macros = {}

    if opts.replace:
        projName = os.path.basename(os.path.dirname(projPath))
        macros = dict(zip(MACROSES, [projName, projPath]))

    # integrate modules

    for dirname in os.listdir(CUR_TPL_FOLDER):
        name = dirname.split(r'_ver=')[0]
        if name in args:
            six.print_(r'use ' + name)
            structToProj(CUR_TPL_FOLDER + dirname, projPath, macros)

    # success
    six.print_(r'Success!')
