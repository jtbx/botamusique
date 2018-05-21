#!/usr/bin/python3

import configparser
import hashlib
import os
import variables as var
import zipfile

__CONFIG = configparser.ConfigParser(interpolation=None)
__CONFIG.read("configuration.ini", encoding='latin-1')

def get_recursive_filelist_sorted(path):
    filelist = []
    for root, dirs, files in os.walk(path):
        relroot = root.replace(path, '')
        if relroot != '' and relroot in __CONFIG.get('bot', 'ignored_folders'):
            continue
        if len(relroot):
            relroot += '/'
        for file in files:
            if file in __CONFIG.get('bot', 'ignored_files'):
                continue
            filelist.append(relroot + file)

    filelist.sort()
    return filelist

# - zips all files of the given zippath (must be a directory)
# - returns the absolute path of the created zip file
# - zip file will be in the applications tmp folder (according to configuration)
# - format of the filename itself = prefix_hash.zip
#       - prefix can be controlled by the caller
#       - hash is a sha1 of the string representation of the directories' contents (which are
#           zipped)
def zipdir(zippath, zipname_prefix=None):
    zipname = __CONFIG.get('bot', 'tmp_folder')
    if zipname_prefix and '../' not in zipname_prefix:
        zipname += zipname_prefix.strip().replace('/', '_') + '_'

    files = get_recursive_filelist_sorted(zippath)
    hash = hashlib.sha1((str(files).encode())).hexdigest()
    zipname += hash + '.zip'

    if os.path.exists(zipname):
        return zipname

    zipf = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)

    for file in files:
        filepath = os.path.dirname(file)
        file_to_add = os.path.join(zippath, file)
        add_file_as = os.path.relpath(os.path.join(zippath, file), os.path.join(zippath, '..'))
        zipf.write(file_to_add, add_file_as)

    zipf.close()
    return zipname

class Dir(object):
    def __init__(self, name):
        self.name = name
        self.subdirs = {}
        self.files = []

    def add_file(self, file):
        if file.startswith(self.name + '/'):
            file = file.replace(self.name + '/', '')

        if '/' in file:
            # This file is in a subdir
            subdir = file.split('/')[0]
            if subdir in self.subdirs:
                self.subdirs[subdir].add_file(file)
            else:
                self.subdirs[subdir] = Dir(subdir)
                self.subdirs[subdir].add_file(file)
        else:
            self.files.append(file)
        return True

    def get_subdirs(self, path=None):
        subdirs = []
        if path and path != '':
            subdir = path.split('/')[0]
            if subdir in self.subdirs:
                searchpath = '/'.join(path.split('/')[1::])
                subdirs = self.subdirs[subdir].get_subdirs(searchpath)
                subdirs = list(map(lambda subsubdir: os.path.join(subdir, subsubdir), subdirs))
        else:
            subdirs = self.subdirs

        return subdirs

    def get_subdirs_recursively(self, path=None):
        subdirs = []
        if path and path != '':
            subdir = path.split('/')[0]
            if subdir in self.subdirs:
                searchpath = '/'.join(path.split('/')[1::])
                subdirs = self.subdirs[subdir].get_subdirs_recursively(searchpath)
        else:
            subdirs = list(self.subdirs.keys())

            for key, val in self.subdirs.items():
                subdirs.extend(map(lambda subdir: key + '/' + subdir,val.get_subdirs_recursively()))

        subdirs.sort()
        return subdirs

    def get_files(self, path=None):
        files = []
        if path and path != '':
            subdir = path.split('/')[0]
            if subdir in self.subdirs:
                searchpath = '/'.join(path.split('/')[1::])
                files = self.subdirs[subdir].get_files(searchpath)
        else:
            files = self.files

        return files

    def get_files_recursively(self, path=None):
        files = []
        if path and path != '':
            subdir = path.split('/')[0]
            if subdir in self.subdirs:
                searchpath = '/'.join(path.split('/')[1::])
                files = self.subdirs[subdir].get_files_recursively(searchpath)
        else:
            files = self.files

            for key, val in self.subdirs.items():
                files.extend(map(lambda file: key + '/' + file,val.get_files_recursively()))

        return files

    def render_text(self, ident=0):
        print('{}{}/'.format(' ' * (ident * 4), self.name))
        for key, val in self.subdirs.items():
            val.render_text(ident+1)
        for file in self.files:
            print('{}{}'.format(' ' * ((ident + 1)) * 4, file))
