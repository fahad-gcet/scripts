import configparser
import imaplib
import email
import re
import os
import pymysql
from dateutil.parser import parse


def db_connect():
	db = pymysql.connect("localhost","root","mindfire","test_db")
	return db


def connect():
	config = configparser.ConfigParser()
	config.read([os.path.expanduser('~/.fahadConfig')])

	hostname = config.get('server', 'hostname')
	port = config.get('server', 'port')

	m = imaplib.IMAP4_SSL(hostname, port)

	username = config.get('account', 'username')
	password = config.get('account', 'password')

	m.login(username, password)
	m.select()

	return m


# Using PEEK so that we don't change the UNREAD status of the email
def getMailByID(m, emailid):
	resp, data = m.fetch(emailid, "(BODY.PEEK[])")
	email_body = data[0][1].decode('utf-8')
	mail = email.message_from_string(email_body)
	return mail


def getMailDetail(m, emailid):
	mail = getMailByID(m, emailid)
	for part in mail.walk():
		if part.get_content_type() == 'text/html':
			html = part.get_payload(decode=True)
	html = html.decode("utf-8")
	# Remove HTML tags
	html = re.sub('<[^<]+?>', '', html)
	# Remove spaces
	body = html.strip()
	
	return mail['from'], mail['to'] ,mail['subject'], body, mail['date']


def downloaAttachmentsInEmail(m, emailid, outputdir, mail_id):
	mail = getMailByID(m, emailid)
	if mail.get_content_maintype() != 'multipart':
		return
	for part in mail.walk():
		if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
			file_path = outputdir + '/' + part.get_filename()
			open(file_path, 'wb').write(part.get_payload(decode=True))
			F = open(file_path,'r')


			db = db_connect()
			cursor = db.cursor()
			sql = "INSERT INTO attachments(mail_id, attachment_path, parsed_data) VALUES ('%s', '%s', '%s')" % (mail_id, os.path.realpath(F.name), F.read())

			try:
				cursor.execute(sql)
				db.commit()
			except Exception as e:
				print(e)
				db.rollback()
			db.close()
			
		


def retreiveEmails(m, outputdir):
	resp, items = m.search(None, '(FROM "fms525@outlook.com" SUBJECT "Final Test Mail")')
	items = items[0].split()
	for emailid in items:
		sender, receiver, subject, body, created_at =  getMailDetail(m, emailid)
		print('FROM: ', sender)
		print('TO: ', receiver)
		print('SUBJECT: ', subject)
		dt = parse(created_at)
		dt = dt.strftime('%Y-%m-%d %H:%M:%S')
		print('CREATED AT: ', dt)
		db = db_connect()
		cursor = db.cursor()
		sql = "INSERT INTO emails(sender, receiver, subject, body, created_at) VALUES ('%s', '%s', '%s', '%s', '%s' )" % (sender, receiver, subject, body, dt)
		try:
			cursor.execute(sql)
			db.commit()
			mail_id = cursor.lastrowid
		except Exception as e:
			print(e)
			db.rollback()
		db.close()
		downloaAttachmentsInEmail(m, emailid, outputdir, mail_id)


if __name__ == '__main__':
	m = connect()
	retreiveEmails(m, './downloads')

