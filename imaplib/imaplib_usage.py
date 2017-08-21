import configparser
import imaplib
import email
import re
import os


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
	print('FROM: ', mail['from'])
	print('SUBJECT: ', mail['subject'])
	for part in mail.walk():
		if part.get_content_type() == 'text/html':
			html = part.get_payload(decode=True)
	html = html.decode("utf-8")
	# Remove HTML tags
	html = re.sub('<[^<]+?>', '', html)
	# Remove spaces
	html = html.strip()
	print('***START BODY ***')
	print(html)
	print('***END BODY ***')

def downloaAttachmentsInEmail(m, emailid, outputdir):
	mail = getMailByID(m, emailid)
	if mail.get_content_maintype() != 'multipart':
		return
	for part in mail.walk():
		if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
			open(outputdir + '/' + part.get_filename(), 'wb').write(part.get_payload(decode=True))


def retreiveEmails(m, outputdir):
	resp, items = m.search(None, '(FROM "fms525@outlook.com" SUBJECT "Final Test Mail")')
	items = items[0].split()
	for emailid in items:
		getMailDetail(m, emailid)
		downloaAttachmentsInEmail(m, emailid, outputdir)


if __name__ == '__main__':
	m = connect()
	retreiveEmails(m, '.')

