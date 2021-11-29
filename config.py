# mysql connection params
mysql_host =  'localhost'
mysql_port = 3306
mysql_db_user = 'boberuser'
mysql_db_password = '123pwd'
mysql_db_name = "mysomefundatabase"

test_backup_tables = {'tables': 'table1,table2,table3'}


# nats connection params
nats_host = 'localhost'
nats_port = 4222

# env params
backupdir = '/opt/backups'
backupfilesextension = '7z'
tmpextractdir = '/tmp/restoredb'