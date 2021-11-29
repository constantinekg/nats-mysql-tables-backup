#!/usr/bin/env python3

import os
import config
import pathlib

# get files by backup extension into dictionary
def getFilesFromDir():
    backdir = config.backupdir
    ext = config.backupfilesextension
    files_dict = {}
    indir_files = []
    backup_files = {}
    try:
        indir_files = (os.listdir(backdir))
    except:
        pass
    if len(indir_files) != 0:
        counter = 0
        for f in indir_files:
            if (pathlib.Path(f).suffix == '.'+ext):
                addfile = {str(counter) : f}
                backup_files.update(addfile)
                counter+=1
            else:
                pass
    else:
        pass
    return backup_files

