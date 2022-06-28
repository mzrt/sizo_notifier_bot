import json
import sqlite3 as sq

# Local imports
from logger import getlogger_initDb as getlogging
from config import config
import datetime
from botusers import load, save
logging = getlogging()

url = config['URL']
urlPeredachi = 'peredachi'
urlPeredachiName = 'Передачи'
urlSvidaniya = 'svidaniya'
urlSvidaniyaName = 'Свидания'
urlType = urlPeredachi if config['URL_TYPE'] == 2 else urlSvidaniya
sizoName = config['SIZO_NAME']
sizoCode = config['SIZO_CODE']
initDbByJSON = config['INITDB_BY_JSON'] == 'true'
dbFileName = config['DB_FILENAME']
userIdFileName = config['USERID_FILENAME']
def insertUpdate(
    cur,
    table,
    wherecondition,
    insertvalkeys,
    insertvals,
    update,
    setExpression,
    params
):
    print(f"select count(*) from {table} where {wherecondition};")
    rowsQty = cur.execute(
        f"select count(*) from {table} where {wherecondition};",
        params
    ).fetchone()[0]
    if rowsQty==0:
        cur.execute(f"INSERT INTO {table}({insertvalkeys}) VALUES({insertvals})", params)
    elif update:
        cur.execute(f"UPDATE {table} set {setExpression} where {wherecondition};", params)

with sq.connect(dbFileName) as conn:
    cur = conn.cursor()
    """ Risons and urls """
    cur.executescript("""
        -- DROP TABLE IF EXISTS collections;
        CREATE TABLE IF NOT EXISTS collections(
            collectionId INTEGER PRIMARY KEY AUTOINCREMENT,
            classId TEXT
        );

        -- DROP TABLE IF EXISTS prisons;
        CREATE TABLE IF NOT EXISTS prisons(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT,
            description TEXT,
            urls INTEGER UNIQUE
        );
        -- DROP TRIGGER IF EXISTS prisons_collection_trigger;
        CREATE TRIGGER IF NOT EXISTS prisons_collection_trigger
            AFTER INSERT ON prisons
            WHEN NEW.urls IS NULL
        BEGIN
            INSERT INTO collections(classId) VALUES('urls');
            UPDATE prisons
            SET urls = (SELECT MAX(collectionId) FROM collections)
            WHERE id = NEW.id;
        END;

        -- DROP TABLE IF EXISTS urls;
        CREATE TABLE IF NOT EXISTS urls(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collectionId INTEGER,
            urltype INTEGER,
            url TEXT UNIQUE,
            UNIQUE (collectionId, urltype)
        );

        -- DROP TABLE IF EXISTS urlTypes;
        CREATE TABLE IF NOT EXISTS urlTypes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            name TEXT
        );
    """)
    insertUpdate(
        cur,
        "urlTypes",
        wherecondition="code=:code",
        insertvalkeys="code, name",
        insertvals=":code, :name",
        update=True,
        setExpression="name=:name",
        params={"code":urlPeredachi, "name": urlPeredachiName}
    )
    insertUpdate(
        cur,
        "urlTypes",
        wherecondition="code=:code",
        insertvalkeys="code, name",
        insertvals=":code, :name",
        update=True,
        setExpression="name=:name",
        params={"code":urlSvidaniya, "name": urlSvidaniyaName}
    )
    insertUpdate(
        cur,
        "prisons",
        wherecondition="code=:code",
        insertvalkeys="code, name",
        insertvals=":code, :name",
        update=True,
        setExpression="name=:name",
        params={"code":sizoCode, "name":sizoName}
    )
    urlsCollection = cur.execute(
        "SELECT urls FROM prisons WHERE code=:code;", {"code":sizoCode}
    ).fetchone()[0]
    insertUpdate(
        cur,
        "urls",
        wherecondition="collectionId=:collectionId " +
            "AND urltype=(select max(id) from urlTypes where code=:urlType)",
        insertvalkeys="collectionId, urltype, url",
        insertvals=":collectionId, (select max(id) from urlTypes where code=:urlType), :url",
        update=True,
        setExpression="url=:url",
        params={"collectionId":urlsCollection, "urlType":urlType, "url": url}
    )

    """ Users """
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY,
            submitedUrls INTEGER UNIQUE,
            subscribes INTEGER UNIQUE,
            logins INTEGER UNIQUE,
            notifyLog INTEGER UNIQUE
        );
        CREATE TRIGGER IF NOT EXISTS users_collection_trigger
            AFTER INSERT ON users
        BEGIN
            INSERT INTO collections(classId) VALUES('submitedurls');
            UPDATE users
            SET submitedUrls = (SELECT MAX(collectionId) FROM collections)
            WHERE id=NEW.id;

            INSERT INTO collections(classId) VALUES('notifylog');
            UPDATE users
            SET notifyLog = (SELECT MAX(collectionId) FROM collections)
            WHERE id=NEW.id;

            INSERT INTO collections(classId) VALUES('subscribes');
            UPDATE users
            SET subscribes = (SELECT MAX(collectionId) FROM collections)
            WHERE id=NEW.id;

            INSERT INTO collections(classId) VALUES('logins');
            UPDATE users
            SET logins = (SELECT MAX(collectionId) FROM collections)
            WHERE id=NEW.id;
        END;
        CREATE TABLE IF NOT EXISTS submitedUrls(
            collectionId INTEGER,
            urlId INTEGER,
            PRIMARY KEY (collectionId, urlId)
        );
        CREATE TABLE IF NOT EXISTS notifyLog(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collectionId INTEGER,
            notifyTime REAL,
            parseLogId INTEGER,
            UNIQUE (collectionId, parseLogId)
        );
        CREATE TABLE IF NOT EXISTS subcribes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collectionId INTEGER,
            urlId INTEGER,
            loginId INTEGER,
            dateStart REAL,
            dateEnd REAL,
            UNIQUE (collectionId, urlId, loginId)
        );
        CREATE TABLE IF NOT EXISTS logins(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collectionId INTEGER,
            login TEXT,
            pass TEXT,
        );
    """)

    """ Parser log """
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parserLog(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urlId INTEGER,
            datetime REAL,
            daysSnapshot TEXT,
            UNIQUE (urlId, datetime)
        );
    """)
    if initDbByJSON :
        userIdValues = load(userIdFileName)
        userIds = list(userIdValues["chatIds"].keys())
        users = list(map(
            lambda userId:  (userId,),
            userIds
        ))
        print(json.dumps(users))
        cur.executemany("INSERT INTO users(id) VALUES(?)", users)
        urlId = cur.execute("SELECT id FROM urls WHERE url=:url;", {"url": url}).fetchone()[0]
        print(f"urlId {urlId}")
        cur.execute("""
            INSERT INTO submitedUrls(collectionId, urlId)
            SELECT submitedUrls, :urlId FROM users
        """, {"urlId": urlId})
        now = datetime.datetime.now()
        insertUpdate(
            cur,
            "parserLog",
            wherecondition="urlId=:urlId",
            insertvalkeys="urlId, datetime, daysSnapshot",
            insertvals=":urlId, :datetime, :daysSnapshot",
            update=False,
            setExpression="",
            params={"urlId":urlId, "datetime":now, "daysSnapshot": "[]"}
        )
        parseLogId = cur.execute(
            "SELECT max(id) FROM parserLog WHERE urlId=:urlId;", {"urlId":urlId}
        ).fetchone()[0]
        cur.execute("""
            INSERT INTO notifyLog(collectionId, notifyTime, parseLogId)
            SELECT notifyLog, :notifyTime, :parseLogId FROM users
        """, {"notifyTime": now, "parseLogId": parseLogId })
