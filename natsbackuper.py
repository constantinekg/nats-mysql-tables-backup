#!/usr/bin/env python3

import asyncio
from nats.aio.client import Client as NATS
import random
import string
import json
import ast
import os
import signal
import sys
import config
import filesutils
import backuper

sys.dont_write_bytecode = True

def handler(signum, frame):
    sys.exit(1)

async def run(loop):
    signal.signal(signal.SIGINT, handler)
    nc = NATS()

    async def disconnected_cb():
        print("Got disconnected...")

    async def reconnected_cb():
        print("Got reconnected...")

    await nc.connect("127.0.0.1",
                     reconnected_cb=reconnected_cb,
                     disconnected_cb=disconnected_cb,
                     max_reconnect_attempts=-1)
    
    # return list of files in backup directory
    async def listBackupsSendedRequest(msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        senddata = {'status' : 'bad'}
        if data == 'listfiles': # If received message with message 'listfiles' - return dictionary with backup archives | return empty if no files found
            senddata = filesutils.getFilesFromDir()
        else:
            pass
        print("Received a message on '{subject} {reply}': {data}".format(
            subject=subject, reply=reply, data=data))
        print(msg.headers)
        await nc.publish(reply, json.dumps(senddata).encode())

    # return backup file detalisation (name of backup file + list of files which inside of archive)
    async def archiveDetail(msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        senddata = {'status' : 'bad'}
        # archivename = msg.headers['archivename']
        # print (archivename)
        if msg.headers == None:
            print('no json found, trying to get archive name from message...')
            archivename = data.replace(' ','').replace('archivename=','')
        else:
            archivename = msg.headers['archivename']
        senddata = backuper.getBackupFileDetails(archivename)
        print("Received a message on '{subject} {reply}': {data}".format(
            subject=subject, reply=reply, data=data))
        # print(msg.headers['archivename'])
        await nc.publish(reply, json.dumps(senddata).encode())
    
    # run backup process
    async def makeBackupSendedRequest(msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        senddata = {'status' : 'bad'}
        backuptables = msg.headers
        if msg.headers == None:
            print ('no json found, trying to get tables from message...')
            backuptables = {'tables':data.replace(' ', '').replace('makebackup=','')}
        else:
            pass
        backuplaunchstatus = backuper.makebackup(backuptables)
        if backuplaunchstatus != False:
            senddata = {'status':'ok','futurefilename':backuplaunchstatus}
        else:
            senddata = {'status':'bad','futurefilename':''}
        print("Received a message on '{subject} {reply}': {data}".format(
            subject=subject, reply=reply, data=data))
        await nc.publish(reply, json.dumps(senddata).encode())

    # run restore process
    async def restoreTablesFromBackup(msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        senddata = {'status' : 'bad'}
        restoredata = msg.headers
        if msg.headers == None:
            print ('no json found, trying to get tables from message...')
            restoredata = {'archivename':data.replace(' ','').split(';')[0].replace('archive=',''),'tables':data.replace(' ','').split(';')[1].replace('tables=','')}
        else:
            pass
        print (restoredata)
        restorestatus = backuper.extractBackupArchive(restoredata['archivename'], restoredata['tables'])
        if restorestatus != False:
            if restorestatus == True:
                senddata = {'status':'ok'}
            else:
                senddata = {'status' : 'bad'}
        else:
            senddata = {'status' : 'bad'}
        print("Received a message on '{subject} {reply}': {data}".format(
            subject=subject, reply=reply, data=data))
        await nc.publish(reply, json.dumps(senddata).encode())

    # Use queue named 'backup.SOMENAME.*' for distributing requests
    # among subscribers.
    await nc.subscribe("backup.makebackup", "workers", makeBackupSendedRequest)
    await nc.subscribe("backup.listbackups", "workers", listBackupsSendedRequest)
    await nc.subscribe("backup.archive", "workers", archiveDetail)
    await nc.subscribe("backup.restore", "workers", restoreTablesFromBackup)

    print("Listening for requests subject...")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.run_forever()
    loop.close()