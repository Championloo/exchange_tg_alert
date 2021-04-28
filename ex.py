from exchangelib import DELEGATE, Account, Credentials, Configuration, CalendarItem, EWSDateTime
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from pprint import pprint
from datetime import datetime, timedelta, timezone
import sqlite3
import telebot
import time
import re

#заполнить своими данными
bot = telebot.TeleBot('0000000:AAAAAAAAAAAAAAAAAAAAAAAAAA') #токен тг-бота
username = 'domen\\username'
password = 'password'
server = 'ex.domen.com'
user_mail = "username@domen.com"
tg_user_id = 000000000

con = sqlite3.connect("ex.db", check_same_thread=False)
cursor = con.cursor()

creds = Credentials(
		username=username,
		password=password
)
BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter
config = Configuration(server=server, credentials=creds)
account = Account(
		primary_smtp_address=user_mail,
		autodiscover=False, 
		config=config,
		access_type=DELEGATE
)

def unread():
	global con, cursor, account
	if account.inbox.unread_count!=0:
		for item in account.inbox.all().order_by('-datetime_received')[:10]:
			if item.is_read==False:
				with con:
					cursor.execute("SELECT DISTINCT * FROM mail WHERE id = ?",(item.message_id,))
					data = cursor.fetchall()
					if len(data)==0:
						cursor.execute('INSERT INTO mail VALUES (?,?)',(item.message_id,datetime.now()))
						con.commit()
						bot.send_message(tg_user_id, f'От кого: {item.sender.name}\n{item.sender.email_address}\nТема: {item.subject}')

def meet():
	global con, cursor, account
	now = datetime.now()
	items = account.calendar.view(
			start=account.default_timezone.localize(EWSDateTime(now.year,now.month,now.day)),
			end=account.default_timezone.localize(EWSDateTime(now.year,now.month,now.day)) + timedelta(days=1),
			)
	for item in items:
		zoom = re.findall('(https://us02web\.zoom\.[/?=\w]+)[";$\s]', item.body+item.location)
		zoom = '\n\n'.join(zoom)
		delta = ((item.start+timedelta(hours=5))-(datetime.now(timezone.utc)+timedelta(hours=5))).total_seconds()
		if 900>=delta>0:
			with con:
				cursor.execute("SELECT DISTINCT * FROM meets WHERE id = ?",(item._id.id,))
				data = cursor.fetchall()
				if len(data)==0:
					cursor.execute('INSERT INTO meets VALUES (?,?,?)',(datetime.now(),item.subject,item._id.id))
					con.commit()
					bot.send_message(tg_user_id, f'Скоро начнётся встреча\n{(item.start+timedelta(hours=5)).strftime("%H:%M")}-{(item.end+timedelta(hours=5)).strftime("%H:%M")} {item.subject}\n\n{zoom}')


while True:
	unread()
	meet()
	time.sleep(60)