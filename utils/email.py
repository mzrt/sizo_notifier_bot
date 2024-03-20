import imaplib
import email
from email.header import decode_header
import re

def getResetPassworCodeWithConfig(config):
    def getResetPassworCode():
        mail_pass = config['EMAIL_PASS']
        username = config['AUTH_LOGIN']
        imap_server = config['imap_server']
        recovery_email_from = config['recovery_email_from']
        imap = imaplib.IMAP4_SSL(imap_server)
        imap.login(username, mail_pass)
        imap.select("INBOX")
        state, messageIdxsString = imap.search(None, 'FROM', f'"{recovery_email_from}"')
        messageIdxs = messageIdxsString[0].split()
        recoveryCode = ''
        if messageIdxs:
            res, msg = imap.fetch(messageIdxs[-1], '(RFC822)')
            message = email.message_from_bytes(msg[0][1])
            subj = decode_header(message['Subject'])[0][0].decode()
            recoveryCode = re.sub('^.*(\d{4}).*$', '\\1', subj)
        return recoveryCode
    return getResetPassworCode