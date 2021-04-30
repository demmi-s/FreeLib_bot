# coding: utf8
#This part of the code handles database queries. 
import sqlite3 as sql
from config import abbreviation_dict, my_bot
from time import time

def search(s):  #this function searches the database 
    try:
        con =sql.Connection("db.sqlite3")
        cur =con.cursor()
        s =str(s)
        for sym in s:   #cleaning of unnecessary characters. if the character is 
            if sym.isalpha() ==False and sym.isdigit()==False: #not a letter or number, 
                s =s.replace(sym, " ") #it will be removed from the query string. 
        if len(s) <3:
            return None
        #This is where a full-text search is performed on the table. 
        cur.execute("SELECT lib.rowid, ban, author, title, translator,\
            seqname, uncompressed, zip, offset, compressed FROM lib INNER Join zip\
        on lib.rowid = zip.rowid WHERE lib MATCH  ? ORDER BY author",(s,))
        res =cur.fetchmany(70)

        return res   #returns a list with tuples. 

    except sql.Error as error:
        print("Ошибка при подключении к sqlite (search) ", error)
        return None
    finally:
        if (con):
            con.close()

def showsize(n):
    n =float(n)
    if n >1048576:
        return " ("+ str(round((n/1024/1024), 2))+" MB.) "
    if n <1048576:
        
        return " ("+ str(round((n/1024), 1))+" KB.) "

#The list with tuples is processed here. 
# and formatting of search results. The function returns a list with lists. 
def searcher(s):
    s =search(s)
    if not s:
        return None
    resultlist =[]
    authors =["",]
    for t in s:
        t =list(t)
        if t[1] ==1:
            #if book in Ban (1 =ban and 0 = not in ban)
            continue
        if len(t[3]) >35: #len. book title field.
            words =t[3].lower().split()
            for n, word in enumerate(words):    #if word is to long,
                if word in abbreviation_dict:
                    word =abbreviation_dict.get(word)
                    words[n]=word               # the word is replaced with a word from the dictionary (config.abbreviation_dict)
                t[3]=" ".join(map(str, words))
        if len(t[3]) >100:
            t[3]=t[3][0:100]+"..."
        if len(t[2].split()) ==2:   # if the author field contains 2 words,
            st =tuple(t[2].split())
            st1 =str(st[0][0]).upper() +". "+str(st[1])# the first word is replaced 
            t[2]=st1 # with one letter. the first letter. 
        if len(t[2]) >60:
            t[2]=t[2][0:60]+"..."
        if len(t[4]) >50:   #Translator.
            t[4] =t[4][0:50]+"..."
        if len(t[4]) >3:
            t[3] = t[3] +"\n Пер.("+t[4]+")"
        if len(t[5]) >70:   # book series.
            t[4] =t[5][0:70]+"..."
        if len(t[5]) >3:
            t[3] =t[3]+"\n Серия: "+t[5]
        t[6] =" "+ showsize(float(t[6])) #formats the file size and displays it in a convenient way. 
        t[3]= "\n" +'📖'+ " "+t[3]+"\n"+str(t[6]) +"\n 👉"+"/"+str(t[0])
        emo = "\n\n" + '   👤' +"  "
        author =t[2]
        author_emo = emo +"  "+t[2]+"\n"
        if author in authors:
            t[2]= "\n"
        if author not in authors:
            authors.append(author)
            t[2]=author_emo

        resultlist.append(t)

    return resultlist

# A search is performed here by row number in the table. 
# the function returns a tuple with the file name(.zip), byte offset 
# and size of the compressed file. 
def search_zip(n):
    try:
        con =sql.Connection("db.sqlite3")
        cur =con.cursor()
        cur.execute("SELECT zip, offset, compressed ,file, c0author, c1title FROM zip \
            Join lib_content on lib_content.rowid =zip.rowid WHERE zip.rowid like ?",(n,))
        res =cur.fetchone()
        if not res:
            return None
        return res
    except sql.Error as error:
        print("Ошибка при подключении к sqlite (search_zip) ", error)
        return None
    finally:
        if (con):
            con.close()

def if_book_in_telegram(n):
    zip_book_filename =search_zip(n)
    if not zip_book_filename:
        return None
    zip_book_filename =zip_book_filename[3]
    try:
        con =sql.Connection("dbuser.sqlite")
        cur =con.cursor()
        if my_bot==0:
            cur.execute("SELECT fileid FROM bot_sending_files WHERE filename_zip \
            LIKE ?",(zip_book_filename,))
        else:
            cur.execute("SELECT msg_chat_id FROM bot_sending_files WHERE filename_zip \
            LIKE ?",(zip_book_filename,))
        res = cur.fetchone()
        con.close()
        if res ==None:
            return None, zip_book_filename

        return res, zip_book_filename
    except sql.Error as error:
        print("can't connect to users.db (if_book_in_telegram )", error)
        if con:
            con.close()
        return None


def create_table_users():
    try:
        con =sql.Connection("dbuser.sqlite")
        cur =con.cursor()
        cur.executescript("CREATE TABLE IF NOT EXISTS users (\
            'userid' INT UNIQUE NOT NULL,\
            'firstname' VARCHAR(100),\
            'lastname' VARCHAR(100),\
            'username' VARCHAR(100),\
            'count' INTEGER DEFAULT 1,\
            'ban' INTEGER NOT NULL DEFAULT 0 ,\
            'dl_bytes'  INTEGER DEFAULT 0,\
            'timestamp' TIMESTAMP); \
                CREATE TABLE IF NOT EXISTS bot_sending_files (\
            'filename' VARCHAR(120),\
            'filename_zip' VARCHAR(120) UNIQUE NOT NULL, \
            'fileid' VARCHAR(120) ,\
            'msg_chat_id' INTEGER,\
            'dl_count' INTEGER DEFAULT 1,\
            'dl_from_telegram' INTEGER DEFAULT 0)")
        con.close()

        return True

    except sql.Error as error:
        print("can't connect to users.db (create_table_users )", error)

        return False

def user_to_database(message):
    user_id =message.from_user.id
    first_name =message.from_user.first_name
    last_name =message.from_user.last_name
    user_name =message.from_user.username
    try:
        con =sql.Connection("dbuser.sqlite")
        cur =con.cursor()
        cur.execute("SELECT userid FROM users WHERE userid =?",(user_id, ))
        a =cur.fetchone()
        if a is not None:
            cur.execute("UPDATE users SET count = count + 1 WHERE userid =?",(user_id,))
            con.commit()
        else:
            cur.execute("INSERT INTO 'users' VALUES (?, ?, ?,\
            ?, ?, ?, ?, ?) ",(user_id, first_name, last_name, user_name, 1, 0, 0,  time().__round__(), ))
            con.commit()
        return True
    except sql.Error as error:
        print("can't connect to users.db (user_to_database)", error)
        if con:
            con.close()
        return False


def user_download(user_id, dl_bytes, book_filename,zip_book_filename, f_id=0, msg_chat_id=0):
    try:
        con =sql.Connection("dbuser.sqlite")
        cur =con.cursor()
        cur.execute("SELECT userid FROM users WHERE userid =?",(user_id, ))
        a =cur.fetchone()
        if a is not None:
            cur.execute("UPDATE users SET dl_bytes = dl_bytes + ? WHERE userid = ? ",(dl_bytes, user_id))
            con.commit()
        cur.execute("SELECT filename_zip FROM bot_sending_files WHERE filename_zip =?",(zip_book_filename,))
        a =cur.fetchone()
        if a is None:
            cur.execute("INSERT INTO 'bot_sending_files' VALUES\
            (?, ?, ?, ?, 0, 0) ",(book_filename, zip_book_filename, f_id, msg_chat_id))
            con.commit()
        cur.execute("UPDATE bot_sending_files SET\
            dl_from_telegram =dl_from_telegram +?, dl_count =dl_count +1 WHERE filename_zip =?", (dl_bytes, zip_book_filename,))
        con.commit()
        con.close()
        return True
    except sql.Error as error:
        print("can't connect to users.db ()user_download)", error)
        if con:
            con.close()
        return False

def user_bannet(n, b=0):
    try:
        con =sql.Connection("dbuser.sqlite")
        cur =con.cursor()
        if b==1:
            cur.execute("UPDATE users SET ban =1 WHERE userid =?",(n,))
            con.commit()
            cur.execute("SELECT ban FROM users WHERE userid LIKE ?",(n,))
            r =cur.fetchone()
            if r ==None:
                return False
            return True
        if b==2:
            cur.execute("UPDATE users SET ban =0 WHERE userid = ?",(n,))
            con.commit()
            cur.execute("SELECT ban FROM users WHERE userid LIKE ?",(n,))
            r =cur.fetchone()
            if r ==None:
                return False
            return True
        cur.execute("SELECT ban FROM users WHERE userid LIKE ?",(n,))
        r =cur.fetchone()
        if not r:
            return False
        con.close()
        if r[0] ==1:
            return True
        return False
    except sql.Error as error:
        print("can't connect to users.db (ban)", error)
        if con:
            con.close()
        return None


def book_to_ban(n, b=1):  #this function searches the database 
    try:
        con =sql.Connection("db.sqlite3")
        cur =con.cursor()
        if b ==1:
            cur.execute("UPDATE zip SET ban =1 WHERE zip.rowid =?", (n,))
            con.commit()
            if cur.rowcount < 1:
                return False
            return True
        if b ==0:
            cur.execute("UPDATE zip SET ban =0 WHERE zip.rowid =?", (n,))
            con.commit()
            if cur.rowcount < 1:
                return False
            return True
        if b==5:
            cur.execute("SELECT ban FROM zip WHERE zip.rowid =?",(n,))
            r =cur.fetchone()
            if not r:
                return None
            return r
        con.close()
        return False
    except sql.Error as error:
        print("Ошибка при подключении к sqlite (book_to_ban) ", error)
        return None
    finally:
        if (con):
            con.close()