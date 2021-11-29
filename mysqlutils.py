#!/usr/bin/env python3

import pymysql
import config


# get all tables names from database - return tables as array | return false
def getAllTablesFromDb():
    try:
        db = pymysql.connect(host=config.mysql_host,user=config.mysql_db_user,password=config.mysql_db_password,database=config.mysql_db_name,charset='utf8mb4')
        cursor = db.cursor()
        cursor.execute("SHOW TABLES")
        data = cursor.fetchall()
        tables = []
        for row in data:
            tables+=row
        return (tables)
    except:
        print ('Error! can\'t fetch data from database')
        return False

# check if tables which we need to check is exists in database - return true if all tables exists | return array of tables which not in db
def checkTablesIsExists(tables):
    print(tables)
    alltables = getAllTablesFromDb()
    if alltables != False:
        checktables = tables.get('tables').split(',')
        not_have = []
        for tab in checktables:
            if tab not in alltables:
                not_have.append(tab)
            else:
                pass
        if len(not_have) > 0:
            return ','.join([str(elem) for elem in not_have])
        else:
            return True

