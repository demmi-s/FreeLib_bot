# coding: utf8
import time
import requests
from zipfile import ZipFile
from zip_inflate import inflate
import io
from db import search_zip, if_book_in_telegram
from config import auth, url


def download_Book(url, offset, compressed_Size, book_filename,zip_book_filename ):
    chunk_size =int(offset)+int(compressed_Size)
    headers = {'Range': 'bytes=%s-%s' % (offset, chunk_size)}
    try: 
        if auth ==None:
            u = requests.get(url,headers=headers, stream =True, timeout=(2, 5))
        else:
            u = requests.get(url,headers=headers, auth=auth, stream =True, timeout=(2, 5))
#        download_resuming_supported = 'bytes' in u.headers.get('Accept-Ranges', '')
#        if not download_resuming_supported:
#            print(f"Error: can't download file {book_filename}! Download resuming is not supported!")
#            return None
    except requests.RequestException as error:
        with open("bot.log.txt", "a", encoding="utf-8") as file_log:
            file_log.write("\n "+ error)
            print("Ошибка в модуле downloader: ",error)
        return None
    file_size =int(u.headers.get('Content-Length'))
    f =io.BytesIO()

    # print(file_size)
    file_size_dl = 0
    block_sz = 8192
    count =0

    while True:
        try:
            buffer = u.raw.read(block_sz)
            if not buffer and file_size_dl < file_size:
                print("\n\nСсервер сбросил соединение. Возобновляю загрузку.\n\n")
                u.headers["Range"] = "bytes=%s-%s" %(file_size_dl, file_size)
                u = requests.get(url,headers, auth=auth, stream =True, timeout=(2, 2))
            elif not buffer:
                break
            file_size_dl += len(buffer)
            f.write(buffer)
        except requests.RequestException as error:
            with open("bot.log.txt", "a", encoding="utf-8") as file_log:
                file_log.write("\n "+ error)
            print("Ошибка в модуле downloader: ",error)
            return None

    buf2 =io.BytesIO()
    try:
        inf =inflate(f.getvalue())
        buf2.write(inf)
        del inf
        del f
    except:
        print("Inflate ERROR.")
        with open("bot.log.txt", "a", encoding="utf-8") as file_log:
            file_log.write("\n"+ time.asctime() + " Inflate ERROR.")
        return None
    buf2.name =book_filename
    buf2.seek(0)

    return (buf2, zip_book_filename)


def searchBook(n):
    zip_And_filename =search_zip(n)
    if zip_And_filename is None:
        print("Error in searchBook! Can't find book rowid={}".format(n))
        return None
    filename =zip_And_filename[-2][0:30]+" - " + zip_And_filename[-1]
    zip_book_filename =zip_And_filename[3]
    link = url + zip_And_filename[0]
    offset =zip_And_filename[1]
    compressed =zip_And_filename[2]
    if len(filename) >100:
        filename =filename[0:100]
    filename +=".fb2"
    d =download_Book(link, offset, compressed, filename, zip_book_filename)
    
    return d

#print(searchBook(2))

