#!/usr/bin/env python3

import filesutils
import mysqlutils
import time
import config
import os
import subprocess
import py7zr
import shutil
from threading import Thread
import json

# Function for make 7z file
def compressSqlFiles(sqlfiles, archivename, tempdir):
    os.chdir(tempdir)
    with py7zr.SevenZipFile(archivename, 'w') as archive:
        for file in sqlfiles.split(' '):
            archive.write(file, file)
    shutil.rmtree(tempdir)

# proceed archive backup process in sub thred
def proceedbackup(tables):
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    global tempdir
    global sqlfiles
    global filearchivename
    filearchivename = config.backupdir+'/'+timestamp+'-backup.7z'
    try:
        tempdir = config.backupdir+'/'+timestamp+'/'
        os.makedirs(tempdir)
        for table in tables:
            with open(tempdir+table+'.sql', "w+") as stdout:
                cmdline = ['mysqldump','-h',config.mysql_host,'-u'+config.mysql_db_user,'-p'+config.mysql_db_password, config.mysql_db_name,table]
                p1 = subprocess.Popen(cmdline, stdout=subprocess.PIPE)
                p2 = subprocess.Popen('cat', stdin=p1.stdout, stdout=stdout)
        sqlfiles = ' '.join(str(e+'.sql') for e in tables)
        Thread(target=compressSqlFiles, args=(sqlfiles, filearchivename, tempdir,)).start() # run compression in separate thread and don't wait and return future file name as soon as posible
        return filearchivename
    except:
        return False

# proceed main backup process
def makebackup(tables):
    checkiftablesexists = mysqlutils.checkTablesIsExists(tables)
    if checkiftablesexists == True:
        tables4backup = tables.get('tables').split(',')
        backuparchiveproceedresult= proceedbackup(tables4backup)
        if backuparchiveproceedresult == False:
            return False
        else:
            return backuparchiveproceedresult
    else:
        return {'notfoundtables':checkiftablesexists}

# get detalisation of archive - it's name & files which inside of
def getBackupFileDetails(backupfile):
    filepath = config.backupdir+'/'+backupfile
    is7zarchive = py7zr.is_7zfile(filepath)
    is7zarchiveencrypted = py7zr.SevenZipFile(filepath).needs_password()
    try:
        py7zr.SevenZipFile(filepath).test()
        iscrcok = True
    except:
        iscrcok = False
    archinfo = py7zr.SevenZipFile(filepath).list()
    emptyfiles = 0
    for i in archinfo:
        if i.is_directory == False and i.uncompressed == 0:
            emptyfiles+=1
    if is7zarchive == True and iscrcok ==True and is7zarchiveencrypted == False and emptyfiles == 0:
        filesinside = py7zr.SevenZipFile(filepath).getnames()
        return {'status':'ok',backupfile:','.join(str(e) for e in filesinside)}
    else:
        return {'status':'bad'}

# restore into mysql db from sql file
def restoreFileIntoDb(exdir,exfiles):
    for xfile in exfiles:
        fullpathname = exdir+xfile
        with open(fullpathname, 'r') as f: 
            command = ['mysql', '-h%s' % config.mysql_host ,'-u%s' % config.mysql_db_user, '-p%s' % config.mysql_db_password, config.mysql_db_name]
            proc = subprocess.Popen(command, stdin = f)
            stdout, stderr = proc.communicate()
    shutil.rmtree(exdir)


# extract files from archive by it's names and restore them into db
def extractBackupArchive(backuparchivename, files):
    global extractfiles
    extractfiles = files.split(',')
    extractarchive = config.backupdir+'/'+backuparchivename
    isok = getBackupFileDetails(backuparchivename)
    if isok[backuparchivename] != 'bad':
        isfilesinarchive = set(files.split(',')).issubset(set(isok[backuparchivename].split(',')))
        if isfilesinarchive == True:
            print('Making extraction of files...')
            extractdir = config.tmpextractdir+'/'+backuparchivename.replace('.7z', '')+'/'
            extractprocesssuccess = 0
            for exfile in files.split(','):
                processextract = py7zr.SevenZipFile(extractarchive).extract(extractdir, exfile)
                if os.path.exists(extractdir+exfile) and os.path.getsize(extractdir+exfile) > 0:
                    pass
                else:
                    extractprocesssuccess+=1
            if extractprocesssuccess != 0:
                print ('files extraction fail or files which has been extracted is empty')
                return {backuparchivename:'bad'}
            else:
                # restoreFileIntoDb(extractdir,extractfiles)
                # for exfile in files.split(','):
                    # global exfile
                Thread(target=restoreFileIntoDb,args=(extractdir,extractfiles)).start()
                    # restoreFileIntoDb(extractdir+exfile)
                return True
        else:
            print ('some files which we need to extract not found in backup archive')
            return {backuparchivename:'bad'}
    else:
        print ('probably backup archive is corrupted')
        return {backuparchivename:'bad'}


# files4extract = 'table1.sql,table2.sql,table3.sql'
# res = extractBackupArchive('2021-11-28_23-49-44-backup.7z',files4extract)
# print(res)

# a = [1,2,3]
# b = [3,1]
# print (set(b).issubset(a))
