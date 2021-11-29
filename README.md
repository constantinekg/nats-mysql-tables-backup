# nats-mysql-tables-backup

Бэкап таблиц mysql 8 через брокер сообщений nats (проверено и работает в ubuntu 20.04, при наличии python 3.8)


**ПРИМЕРЫ:**
Ниже приводятся примеры, которые приводятся на примере использования набора утилит nats-examples (https://github.com/nats-io/go-nats-examples/releases/download/0.0.50/go-nats-examples-v0.0.50-linux-amd64.zip)

---

**Получение списка ранее созданных файлов архивов резервных копий:**
```
    ./nats-req backup.listbackups "listfiles"
```

Результат выполнения:

```
    Published [backup.listbackups] : 'listfiles'
    Received  [_INBOX.NCUWVOrx7SHW05sSy4xVWo.K60eWp7p] : '{"0": "somebackup.7z"}'
```

***В случае невозможности получения списка:***

```
    ./nats-req backup.listbackups "listfiles"
```
Результат выполнения:
```
    Published [backup.listbackups] : 'listfiles'
    Received  [_INBOX.Boy8V1VInXgyEl1dkjmpcy.Jisakt3I] : '{}'
```
^ пустой список

---

**Создание бэкапа:**

***Создать архив с резервными копиями таблиц можно двумя способами:***

1. При запросе необходимо передать параметр headers={json}, где формат json объекта должен представлять из себя {'tables':'table1,table2...'}.В json объекте передаются имена таблиц, которые необходимо поместить в архив резервной копии. Соответствующий запрос на языке python выглядеть будет так:

```
nc.request("backup.makebackup", 'makebackup'.encode(), headers={'tables':'table1,table2,table3'})
```

Формирование подобного запроса на других языках необходимо уточнять.
1. Список файлов можно передать в сообщении через знак =. К примеру запрос, выполняемый через nats-req:
```   
./nats-req backup.makebackup "makebackup=table1,table2,table3"
```
Результат выполнения:

```
Published [backup.makebackup] : 'makebackup=table1,table2,table3'
Received  [_INBOX.GFb3Zj69O4ieT3CTo6NIrs.Nzz5ApkM] : '{"status": "ok", "futurefilename": "/opt/backups/2021-11-28_17-59-19-backup.7z"}'
```

В случае достижения успешного результата в ответе будет получен json в виде {"status": "ok", "futurefilename": "/opt/backups/2021-11-28_17-59-19-backup.7z"}, где status - ok (процесс был запущен; futurefilename - /opt/backups/2021-11-28_17-59-19-backup.7z (обещаемое имя файла после успешного завершения процесса резервного копирования)).

В случае краха процесса будет возвращён json в виде {'status':'bad','futurefilename':''}, где status - bad (ой всё плохо); futurefilename - '' (пустая строка с обещанным файлом).
Процесс создания архива производится в отдельном потоке, дабы быстрее отдать статус запрашиваемому, не удерживая соединения (дабы не отвалилось по таймауту).

---

**Получение содержимого архива резервной копии:**

Получить можно двумя способами:
1. Разместить имя запрашиваемого архива в заголовке headers в теле запроса. Пример на языке python ниже, для остальных языков необходимо уточнение:

```
nc.request("backup.archive", 'archive'.encode(), headers={'archivename':'2021-11-28_20-30-39-backup.7z'})
```
2. Разместить имя архива в теле сообщения через знак =. Пример с клиентом nats-req:
```
./nats-req backup.archive "archivename=wrong.7z"
```

В случае успешного получения информации будет возвращён список файлов, содержащихся в архиве. Пример:
```
./nats-req backup.archive "archivename=2021-11-28_20-30-39-backup.7z"
Published [backup.archive] : 'archivename=2021-11-28_20-30-39-backup.7z'
Received  [_INBOX.RJtuKZcqC65JAEWy8gMV6A.RQ5cYzMA] : '{"2021-11-28_20-30-39-backup.7z": "table1.sql,table2.sql,table3.sql"}'
```

В случае если архив невозможно прочитать (его не существует, он повреждён или он не является 7z архивом) будет возвращено:
```
./nats-req backup.archive "archivename=2021-11-28_20-30-39-backupf.7z"
Published [backup.archive] : 'archivename=2021-11-28_20-30-39-backupf.7z'
Received  [_INBOX.CnPNfscvrTQjoMlakfzVJe.15UZxvuk] : '{"2021-11-28_20-30-39-backupf.7z": "bad"}'
```

---

**Восстановление таблиц в БД из резервных копий**

Восстановить таблицы возможно двумя способами:

1. Разместить имя запрашиваемого архива и перечень таблиц, необходимых для восстановления в заголовке headers. Пример на языке python, для остальных языков необходимо уточнять:

```
nc.request("backup.restore", 'archive'.encode(), headers={'archivename':'2021-11-28_23-49-44-backup.7z','tables':'table1.sql,table2.sql,table3.sql'})
```

2. Разместить имя архива и имена таблиц в теле сообщения. В качестве разделителя между именем файла и перечнем таблиц служит - ; , а для указания имени архива и имён таблиц - = . Пример с клиентом nats-req:

```
./nats-req backup.restore "archive=2021-11-28_23-49-44-backup.7z;tables=table1.sql,table2.sql,table3.sql"
```

Восстановление производится в отдельном потоке, т.к. процесс может занять приличное время, поэтому ответ производится как можно раньше. В случае успешного запуска процесса восстановления будет получено (пример):

```
Received  [_INBOX.tNRLxow09f16DSeyRXYf6A.tNRLxow09f16DSeyRXYfAG]: '{"status": "ok"}'
<Msg: subject='backup.restore' reply='_INBOX.tNRLxow09f16DSeyRXYf6A.tNRLxow09f16DSeyRXYfAG' data='archive...'>
```

```
./nats-req backup.restore "archive=2021-11-28_23-49-44-backup.7z;tables=table1.sql,table2.sql,table3.sql"
Published [backup.restore] : 'archive=2021-11-28_23-49-44-backup.7z;tables=table1.sql,table2.sql,table3.sql'
Received  [_INBOX.Y3K4HT267jQS6xDsI26F3z.6oVGfVpL] : '{"status": "ok"}'
```

В случае невозможности восстановления в выводе будет фигурировать {'status':'bad'}. Пример:

```
./nats-req backup.restore "archive=2021-11-28_23-49-44-backup.7z;tables=table1.sql,table2.sql,table3.sqld"
Published [backup.restore] : 'archive=2021-11-28_23-49-44-backup.7z;tables=table1.sql,table2.sql,table3.sqld'
Received  [_INBOX.DzRdPAG7u1Ew3ueQ8M6b0C.lOgyRqBl] : '{"status": "bad"}'
```

---

**При использовании, в коде где будет использоваться данное решение  лучше прописать исключение, что может быть получено что то неожиданное в плане вывода.**
