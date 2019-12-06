import os
import shutil
import urllib2
from zipfile import ZipFile
from optparse import OptionParser

# utils

def file_get_contents(filename):
    if not(os.path.exists(filename)):
        return False
    with open(filename, r'r') as f:
        return f.read()

def file_write_contents(filename, content, mode = r'w'):
    if not(os.path.exists(filename)):
        return
    with open(filename, mode) as f:
        f.write(content)

# consts

SERVER_URL = r'https://raw.githubusercontent.com/sigdev/prosys/master/'
TPL_VERSION_FILE = r'TEMPLATES_VERSION'
TPL_ARCHIVE = r'templates.zip'
TPL_FOLDER = r'templates/'

# parse args

parser = OptionParser(usage=r'usage: %prog [options] module1 module2')
parser.add_option(r'-o', r'--out', dest=r'dirname', help=r'create or check project in DIRNAME', metavar=r'DIRNAME')
parser.add_option(r'-l', r'--list', action=r'store_true', dest=r'showlist', help=r'show modules list', default=False)

(options, args) = parser.parse_args()

# check updates templates

server_tpl_version = 0
for line in urllib2.urlopen(SERVER_URL + TPL_VERSION_FILE):
    server_tpl_version=int(line)

current_tpl_version = file_get_contents(r'./' + TPL_VERSION_FILE)
if current_tpl_version == False or not(os.path.exists(r'./' + TPL_FOLDER)):
    current_tpl_version = 0
else:
    current_tpl_version = int(current_tpl_version)

if server_tpl_version == 0 and current_tpl_version == 0:
    print r'ERROR: Current and remote versions of templates is broken. Can not restore template version!'
    exit()

if server_tpl_version > current_tpl_version:
    file_write_contents(r'./' + TPL_VERSION_FILE, str(server_tpl_version))
    filedata = urllib2.urlopen(SERVER_URL + TPL_ARCHIVE)
    datatowrite = filedata.read()
    file_write_contents(r'./' + TPL_ARCHIVE, datatowrite, r'bw')
    if os.path.exists(r'./' + TPL_FOLDER):
        shutil.rmtree(r'./' + TPL_FOLDER)
    with ZipFile(r'./' + TPL_ARCHIVE, r'r') as zipObj:
        zipObj.extractall()