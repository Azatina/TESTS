import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from itertools import cycle

'''
msg = MIMEMultipart()
msg['From'] = 'atereg@tst.local'
msg['To'] = 'azat_test@tst.local'
msg['Subject'] = 'simple email in python'
message = 'here is the email12312312312356785678567'
msg.attach(MIMEText(message))

mailserver = smtplib.SMTP('localhost', 2525)
# identify ourselves to smtp gmail client
mailserver.ehlo()
# secure our email with tls encryption
# mailserver.starttls()
# re-identify ourselves as an encrypted connection
mailserver.ehlo()
# mailserver.login('atereg@tst.local', 'F4W-Aj0f')

mailserver.sendmail('atereg@tst.local', 'azat_test@tst.local', msg.as_string())

mailserver.quit()'''

smtpServer = '192.168.1.203'
fromAddr = 'from@fromaddress.com'
# toAddr = ['aaa@aaa.com', 'bbb@bbb.com', 'ccc@ccc.com',
#          'BAD@example.com', 'fff@fff.com', 'ggg@ggg.com',
#          'yyy@yyy.com', 'zzz@zzz.com']
toAddr = ['to@fromaddress.com']
text = "This is a test of sending email from within Python."
server = smtplib.SMTP(smtpServer, 8025)
server.ehlo()
server.set_debuglevel(1)
server.sendmail(fromAddr, toAddr, text)
server.quit()
