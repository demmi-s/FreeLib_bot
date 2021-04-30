# coding: utf8
from telebot import *
import time
from db import searcher, user_to_database, user_download, create_table_users, if_book_in_telegram, user_bannet, book_to_ban
from downloader import searchBook
import io
import datetime
from config import channel1_chatid, token, admin_list, day_limit_download, day_limit_search, bot_name

bot = TeleBot(token)

''' logger = logger
formatter = logging.Formatter('[%(asctime)s] %(thread)d {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                                  '%m-%d %H:%M:%S')
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)  # or use logging.INFO
ch.setFormatter(formatter)
 '''

create_table_users()

search_count =0
t =int(time.time().__round__())
dl_books_count =0

mess = {}
search_mes ={}
mess_time = datetime.date.today()


def limit_dl(user_id, dl=0):
#    if user_id in admin_list:
 #       return False
    global mess; global mess_time; global search_mes

    def count_mes(c):    
        count = c + 1
        return count

    mode ={1:mess,0:search_mes}
    limit =100
    text = "Превышен дневной лимит на поисковые запросы!\n Я вам не Гугл 😃 \n  Попробуйте  "
    if dl ==0:   limit =day_limit_download; text = "Превышен дневной лимит на скачивание книг! Зачем вам запас? Я всегда под рукой. Я же не могу работать \nтолько на вас😊 Попробуйте "
    else:   limit =day_limit_search
    if mess_time != datetime.date.today():
        mess = {}
        search_mes ={}
        mess_time = datetime.date.today()
    if user_id not in mode[dl]: 
        mode[dl][user_id] = 0
    if mode[dl][user_id] == limit:
        bot.send_message(user_id, text+str(datetime.date.today() + datetime.timedelta(days=1)))
        mode[dl][user_id] = count_mes(mode[dl][user_id])
    if mode[dl][user_id] > limit:
        return True
    else:
        mode[dl][user_id] = count_mes(mode[dl][user_id])

    return False


def verify(message):
    if message.text ==None:
        return False
    len_message =len(message.text)
    if "/download" in message.text[0:10]:
        bot.send_message(message.chat.id, "Хватит слать всякую херню!!!")
        return False
    if message.forward_from_message_id !=None or message.forward_from !=None:
        bot.send_message(message.chat.id, "Вы задолбали уже! хватит пересылать мне всякую хрень! Если хотите пользоваться ботом, можно же формировать нормальные запросы. просто добавьте его в группу и обращайтесь к боту, как указано в правилах Телеграм.!!!\n Ну а если вы обычный пользователь, и у вас просто случайно вышло, то все ок! просто пишите мне напрямую:\n@Book_dl_bot")
        return False
    if len_message >100:
        bot.send_message(message.chat.id, "Ох и длиннющее сообщение... Вы что решили тут роман написать? Не буду я искать.")
        return False

    return True
    
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я умею искать книги.")


@bot.message_handler(content_types=['document'])
def handle_docs(message):
    chat_id = message.chat.id
    doc_name =message.document.file_name
    bot.send_message(chat_id, "Благодарю за книгу: "+doc_name+"\nОбязательно почитаю на досуге!")
    #file_info = bot.get_file(message.document.file_id)
    return True

@bot.message_handler(content_types=["audio", "photo", "sticker", "video", "location", "contact","voice"])
def all_hernya(hernya):
    bot.send_message(hernya.chat.id, "Спасибо! Я перешлю это владельцу бота! Можете присылать свои видосики, аудио-сообщения, музычку хорошую и всякую другую херню...")
    msg_id_from_chat =hernya.message_id
    bot.forward_message(channel1_chatid, hernya.chat.id, msg_id_from_chat)
    return True


@bot.message_handler(commands=['ban','unban', 'bookban', 'bookunban', 'bookstatus'])
def ban(message):
    user_id =message.from_user.id
    if user_id not in admin_list:
        return True
    m =message.text
    command_and_id =m.split()
    if len(command_and_id) ==1:
        return True
    n =command_and_id[1]
    command =command_and_id[0]
    if command =='/ban':
        b = user_bannet(n, 1)
        if b:
            bot.send_message(message.chat.id, 'Пользователь с id: {} успешно забанен!'.format(n))
        else:   bot.send_message(message.chat.id, 'Пользователя с id: {} не существует в базе!!!'.format(n))
    if command =='/unban':
        b =user_bannet(n, 2)
        if b:
            bot.send_message(message.chat.id, 'Пользователь с id: {} помилован!'.format(n))
        else:   bot.send_message(message.chat.id, 'Пользователя с id: {} не существует в базе!!!'.format(n))
    if command =="/bookban":
        b =book_to_ban(n)
        if b:
            bot.send_message(message.chat.id, 'Книга с id: {} добавлена в бан.'.format(n))
        else: bot.send_message(message.chat.id, 'Книги с id: {} нет в базе!!!'.format(n))
    if command =="/bookunban":
        b =book_to_ban(n, 0)
        if b:
            bot.send_message(message.chat.id, 'Книга с id: {} разбанена! :-)'.format(n))
        else: bot.send_message(message.chat.id, 'Книги с id: {} нет в базе!!!'.format(n))
    if command =="/bookstatus":
        b =book_to_ban(n, 5)
        if b:
            bot.send_message(message.chat.id, '{}'.format(b[0]))
        else:   bot.send_message(message.chat.id, 'Book not found.')


@bot.message_handler(func =lambda m: m.text[0] =="/" and m.text[1:7].isdigit() ==True)
def upload_file(message):
    global t; global dl_books_count; global search_count
    user_id =message.from_user.id
    if limit_dl(user_id):
        return True
    ban =user_bannet(user_id)
    if  ban ==True:
        return True
    book_rowid =int(message.text[1:7])
    if book_rowid >500000:
        return True
    result =()
    book_already = if_book_in_telegram(book_rowid)
    if book_already ==None:
        return True
    if book_already[0] !=None:
        doc =bot.send_document(message.chat.id,book_already[0][0])
        book_size =doc.document.file_size
        f_name =doc.document.file_name
        user_download(user_id, book_size, f_name, book_already[1])
        return True
    else:
        result =searchBook(book_rowid)
    if result is None:
        print("Error: File not downloading!")
        bot.send_message(message.chat.id, "Извините, файлохранилище недоступно. Мы решаем проблему!!")
    else:
        f =result[0]
        doc =bot.send_document(message.chat.id,f)
        if len(result) ==2:
            f_id =doc.document.file_id
            doc_to_chat =bot.send_document(channel1_chatid,f_id)
            msg_id_from_chat =doc_to_chat.message_id
            # bot.forward_message(message.chat.id, channel1_chatid, msg_id_from_chat)
            book_size =f.__sizeof__()
            f_name =f.name
            del f
            user_download(user_id, book_size, f_name, result[1],\
            f_id , msg_id_from_chat)
            dl_books_count +=1
            t2 =int(time.time().__round__())
            print("\rr. count:", search_count, " from start to last request: ",datetime.timedelta(seconds=t2 -t), " dl from server: ",dl_books_count, end="")
    return True


@bot.message_handler(content_types=["text"])
def searcher_books(message):
    global search_count; global t; global dl_books_count
    user_id =message.from_user.id
    add_user =user_to_database(message)
    ban =user_bannet(message.from_user.id)
    search_count +=1
    if  ban ==True:
        return True
    if limit_dl(user_id, 1):
        return True
    verify_message = verify(message)
    if verify_message == False:
        return True
    len_bot_name =len(bot_name)
    len_message =len(message.text)
    if len_message > len_message - len_bot_name + 2 and message.text[len_message - len_bot_name:] == bot_name:
        message.text =message.text.replace(bot_name, "")
        if  message.text[1:].strip().isdigit() ==True:
            upload_file(message)
            return True
    search_list =searcher(message.text)
    result_string ="По вашему запросу ничего не найдено 😭"
    if not search_list or len(search_list) ==0:
        bot.send_message(message.chat.id, result_string)
        #bot.delete_message(message.chat.id, message_id=message.message_id)        
    else:
        if len(search_list) >0:    result_string =""
        for i in search_list:
            result_string ="".join(result_string + str(i[2])+str(i[3]))
            if len(result_string) >3800:
                bot.send_message(message.chat.id, result_string)
                result_string =""
        if len(result_string) >0:
            bot.send_message(message.chat.id, result_string)
    t2 =int(time.time().__round__())
    print("\rr. count:", search_count, " from start to last request: ",datetime.timedelta(seconds=t2 -t), " dl from server: ",dl_books_count, end="")
    msg_id_from_chat =message.message_id
    bot.forward_message(channel1_chatid, message.chat.id, msg_id_from_chat)
    
    return True


if __name__ == '__main__':
    bot.infinity_polling()