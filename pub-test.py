#!/usr/bin/env python3

import asyncio
import nats
import config
import random

async def main():
    nc = await nats.connect("nats://"+config.nats_host+":"+str(config.nats_port))
    inbox = nc.new_inbox()
    sub = await nc.subscribe("backup.*")

    # Publish with a reply
    request_queue_random_hash = str(random.getrandbits(128))
    # future = nc.request("backup.listbackups", 'hello'.encode(), headers={'req':'444'}) # EXAMPLE
    try:
        future = nc.request("backup.makebackup", 'makebackup'.encode(), headers={'tables':'table1,table2,table3'}) # EXAMPLE
        # future = nc.request("backup.listbackups", 'listfiles'.encode()) # List backup files in backup dir
        # future = nc.request("backup.archive", 'archive'.encode(), headers={'archivename':'2021-11-28_20-30-39-backup.7z'}) # List backup archive detail - file name and it's content
        # future = nc.request("backup.restore", 'archive'.encode(), headers={'archivename':'2021-11-28_23-49-44-backup.7z','tables':'table1.sql,table2.sql,table3.sql'})
        msg = await future
        subject = msg.subject
        data = msg.data.decode()
        print(f"Received  [{subject}]: '{data}'")
    except:
        print('Error! no data has been received')


    while True:
        try:
            msg = await sub.next_msg()
            print(msg)
        except:
            break
        # print("----------------------")
        # print("Subject:", msg.subject)
        # print("Reply  :", msg.reply)
        # print("Data   :", msg.data)
        # print("Headers:", msg.header)

if __name__ == '__main__':
    asyncio.run(main())
