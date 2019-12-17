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
import datetime
import re
from zipfile import ZipFile
from optparse import OptionParser

iprint = six.print_

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


def list_files_rec(src, stack=r'', is_end=True):
    global iprint
    indent = r'└── ' if is_end else r'├── '
    if src.endswith(r'/') or src.endswith('\\'):
        src = src[:-1]
    iprint(stack + indent + os.path.basename(src))
    stack += r'│   ' if not(is_end) else r'    '
    if os.path.isdir(src):
        chl = os.listdir(src)
        last = len(chl) - 1
        for contens in enumerate(chl):
            list_files_rec(src + os.sep + contens[1],
                           stack, contens[0] == last)


def printProgressBar(message, total, pos,
                     decimals=1, length=50, fill=r'█', printEnd='\r'):
    value = 100 * (pos / float(total))
    percent = (r'{0:.' + str(decimals) + r'f}').format(value)
    filledLength = int(length * pos // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    iprint('\r %s |%s| %s%%' % (message, bar, percent), end=printEnd)
    if pos >= total:
        iprint()


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

    try:
        s = open(filename).read(512)
        text_characters = r''.join(map(chr, range(32, 127))) + '\n\r\t\b'
        if not s:
            return True
        if '\0' in s:
            return False
        t = translate(s, text_characters)
        return float(len(t))/float(len(s)) >= 0.70
    except BaseException:
        return False
    return True


def file_get_contents(filename):
    if not(os.path.exists(filename)):
        return False
    with open(filename, r'r') as f:
        return f.read()


def file_write_contents(filename, content, mode=r'w'):
    with open(filename, mode) as f:
        f.write(content)


def extended_filename(ext, path):
    name, oldext = os.path.splitext(os.path.basename(path))
    return name + r'.' + ext + oldext


# consts

SERVER_URL = r'https://raw.githubusercontent.com/sigdev2/prosys/master/'
TPL_VERSION_FILE = r'TEMPLATES_VERSION'
TPL_ARCHIVE = r'templates.zip'
TPL_FOLDER = r'templates/'

CUR_TPL_VERSION_FILE = r'./' + TPL_VERSION_FILE
CUR_TPL_ARCHIVE = r'./' + TPL_ARCHIVE
CUR_TPL_FOLDER = r'./' + TPL_FOLDER

SRC_FOLDER_NAME = r'src'

LICENSE_LIST = [r'0BSD', r'AFLv3', r'AGPLv3', r'APACHEv2', r'ARTISTICv2',
                r'BSDv2', r'BSDv3', r'BSDv3C', r'BSDv4', r'BSL', r'CC0',
                r'CCv4', r'CCbySAv4', r'CECILLv2-1', r'ECLv2', r'EPL',
                r'EPLv2', r'EUPLv1-1', r'EUPLv1-2', r'GPLv2', r'GPLv3',
                r'ISC', r'LGPLv2-1', r'LGPLv3', r'LPPLv1-3', r'MIT',
                r'MPLv2', r'MSPL', r'MSRL', r'NCSA', r'ODBL', r'OFLv1-1',
                r'OSLv3', r'POSTGRESQL', r'UNLICENSE', r'UPL', r'WTFPLv2',
                r'ZLIB']

RE_IS_LOCALE = re.compile(r'^[A-z]{2}[-_][A-z]{2}$')
RE_IS_VERSION = re.compile(
    r'^\d+[-\._]\d+[-\._]\d+' +
    r'([-\._](a|alpha|b|beta|rc|r|d|debug|release|t|test)([-\._]\d+)?)?$')
RE_IS_LICENSE = re.compile(r'^(' + r'|'.join(LICENSE_LIST) + r')$')
RE_IS_EMAIL = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

MACROSES = {
    r'%%=PROJ_NAME%%': lambda path, projPath, tags:
        os.path.basename(os.path.dirname(projPath)),
    r'%%=PROJ_PATH%%': lambda path, projPath, tags: projPath,
    r'%%=CUR_DATE%%': lambda path, projPath, tags:
        datetime.datetime.now().strftime(r'%Y.%m.%d'),
    r'%%=CUR_YEAR%%': lambda path, projPath, tags:
        datetime.datetime.now().strftime(r'%Y'),
    r'%%=CUR_TIME%%': lambda path, projPath, tags:
        datetime.datetime.now().strftime(r'%H:%M'),
    r'%%=DATE_AS_NUMBER%%': lambda path, projPath, tags:
        datetime.datetime.now().strftime(r'%Y%m%d'),
    r'%%=VERSION%%': lambda path, projPath, tags:
        ([t for t in tags if RE_IS_VERSION.match(t)] + [r'0.1.0-a1'])[0],
    r'%%=LINKS_TO_LOCALIZED%%': lambda path, projPath, tags:
        r' '.join([r'[%s](%s)' % (x, extended_filename(x, path))
                 for x in [t for t in tags if RE_IS_LOCALE.match(t)]]),
    r'%%=LICENSE%%': lambda path, projPath, tags:
        ([t for t in tags if RE_IS_LICENSE.match(t)] + [r'UNLICENSE'])[0],
    r'%%=LINK_TO_LICENSE%%': lambda path, projPath, tags:
        r' '.join([r'[%s](%s)' % (x, extended_filename(x, path))
                  for x in [t for t in tags if RE_IS_LICENSE.match(t)]]),
    r'%%=EMAIL%%': lambda path, projPath, tags:
        ([t for t in tags if RE_IS_EMAIL.match(t)] + [r'[email]'])[0]}


# functions

def structToProjRec(src, target, root, tags, replace):
    global MACROSES
    for contens in os.listdir(src):
        if contens.startswith(r'@'):
            find = False
            for t in tags:
                if contens.endswith(r'.' + t) or (r'.' + t + r'.') in contens:
                    find = True
                    break
            if find is False:
                continue
        full = src + os.sep + contens
        path = target
        path += os.sep + (contens[1:] if contens.startswith(r'@') else contens)
        if os.path.isdir(full):
            if not(os.path.exists(path)):
                os.makedirs(path)
            structToProjRec(full, path, root, tags, replace)
        else:
            if not(os.path.exists(path)):
                shutil.copyfile(full, path)
                if replace and is_text_file(path):
                    c = file_get_contents(path)
                    for macro in MACROSES:
                        c = c.replace(macro,
                                      MACROSES[macro](path, root, tags))
                    file_write_contents(path, c)


if __name__ == r'__main__':

    # parse args

    usage = r'usage: %prog [options] module1 module2 tag1 tag2'
    parser = OptionParser(usage=usage,
                          version='%prog 0.1')
    parser.add_option(r'-o', r'--out',
                      dest=r'proj',
                      help=r'create or check project in DIRNAME',
                      metavar=r'DIRNAME')
    parser.add_option(r'-s', r'--src',
                      action=r'store_true',
                      dest=r'move',
                      help=r'move proj folder content to src folder',
                      default=False)
    parser.add_option(r'-l', r'--list',
                      action=r'store_true',
                      dest=r'showlist',
                      help=r'show modules list')
    parser.add_option(r'-m', r'--macroses',
                      action=r'store_true',
                      dest=r'showmacroses',
                      help=r'show list or macroses to replace in files',
                      default=False)
    parser.add_option(r'-i', r'--license',
                      action=r'store_true',
                      dest=r'showlicense',
                      help=r'show list of available licenses',
                      default=False)
    parser.add_option(r'-R', r'--no_replace',
                      action=r'store_true',
                      dest=r'no_replace',
                      help=r'replace macroses in copyed template files',
                      default=False)
    parser.add_option(r'-d', r'--disable',
                      action=r'store_true',
                      dest=r'disable',
                      help=r'disable templates update',
                      default=False)
    parser.add_option(r'-n', r'--no_results',
                      action=r'store_true',
                      dest=r'no_results',
                      help=r'do not show results',
                      default=False)
    parser.add_option(r'-q', r'--quiet',
                      action=r'store_true',
                      dest=r'quiet',
                      help=r'silent mode',
                      default=False)

    (opts, args) = parser.parse_args()

    if opts.quiet:
        def tmp_print(x=r'', end=r''):
            return False
        iprint = tmp_print

    iprint(r'')

    # list of licenses

    if opts.showlicense:
        iprint('List of available licenses: \n')
        for l in LICENSE_LIST:
            iprint(l)
        iprint('\n')
        os._exit(1)

    # list of macroses

    if opts.showmacroses:
        iprint('List of macroses to replace in templates: \n')
        for m in MACROSES:
            iprint(m)
        iprint('\n')
        os._exit(1)

    # check updates templates

    server_tpl_version = 0
    if not opts.disable:
        res = urlopen(SERVER_URL + TPL_VERSION_FILE)
        server_tpl_version = int(chunkedDownload(TPL_VERSION_FILE, res))

    current_tpl_version = file_get_contents(CUR_TPL_VERSION_FILE)
    if current_tpl_version is False or not(os.path.exists(CUR_TPL_FOLDER)):
        current_tpl_version = 0
    else:
        current_tpl_version = int(current_tpl_version)

    if server_tpl_version == 0 and not(os.path.exists(CUR_TPL_FOLDER)):
        iprint(r'ERROR: Current and remote versions of templates ' +
                   r'is broken. Can not restore template version!')
        os._exit(1)

    updated = False
    if server_tpl_version > current_tpl_version:
        iprint(r'Update templates ...')
        try:
            file_write_contents(CUR_TPL_VERSION_FILE, str(server_tpl_version))
            res = urlopen(SERVER_URL + TPL_ARCHIVE)
            datatowrite = chunkedDownload(TPL_ARCHIVE, res)
            file_write_contents(CUR_TPL_ARCHIVE, datatowrite, r'bw')
            if os.path.exists(CUR_TPL_FOLDER):
                shutil.rmtree(CUR_TPL_FOLDER)
            with ZipFile(CUR_TPL_ARCHIVE, r'r') as zipObj:
                zipObj.extractall()
            iprint(r'Templates update successfully!')
            updated = True
        except BaseException:
            iprint(r'ERROR: Can not update templates! Try skip update ...')
            if not(os.path.exists(CUR_TPL_FOLDER)):
                iprint(r'ERROR: Templates is not exists!')
                os._exit(1)

    # list of templates

    templatesList = os.listdir(CUR_TPL_FOLDER)

    if opts.showlist or updated:
        iprint('List of available templates: \n')
        iprint('    Name:\tVersion:\n')
        for dirname in templatesList:
            iprint(r'    ' + dirname.replace(r'_ver=', '\t'))
        iprint('\n')
        if opts.showlist:
            os._exit(1)

    # applay proj path

    if not opts.proj:
        iprint(r'ERROR: Specify the path to the project!')
        os._exit(1)

    iprint('\nStart working ... \n')

    projPath = os.path.abspath(opts.proj)
    if not(projPath[-1] == os.sep):
        projPath += os.sep

    if not(os.path.exists(projPath)):
        os.makedirs(projPath)
        iprint(r'Projcet directory created !\n')
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

    # parse args

    tags = set()
    templates = set()

    templatesNames = [x.split(r'_ver=')[0] for x in templatesList]

    for name in args:
        if name in templatesNames:
            templates.add(templatesNames.index(name))
        else:
            tags.add(name)

    # integrate modules

    for i in templates:
        iprint(r'use ' + templatesNames[i])
        structToProjRec(CUR_TPL_FOLDER + templatesList[i], projPath,
                        projPath, list(tags), not(opts.no_replace))

    # display result

    if opts.no_results is False:
        iprint('\nResult:\n')
        list_files_rec(projPath)

    # success
    iprint('\nSuccess!')
