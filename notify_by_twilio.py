import imapclient
import pyzmail
import imaplib
import time
from dotenv import load_dotenv
import os
from twilio.rest import Client

load_dotenv()  # Load env variables (dotenv 3rd party module)
imaplib._MAXLINE = 1000000  # Extend limitation for reading arbitrary length lines.


class MailListener:
    def __init__(self):
        self.my_email = os.getenv("MY_EMAIL")  # My email address
        self.pwd = os.getenv("EMAIL_PASSWORD")  # Password for email account
        self.check_timer = 5  # How frequently to check for emails in seconds
        self.imap_client = None  # Stay here as None for init script
        self.wait_for_email = ['goranmrd@gmail.com', 'aaron@cleverprogrammer.com']  # Get twilio sms for msgs from these emails

    def run(self):
        while True:  # Main loop
            self.imap_init()
            print("Listening for new messages...")
            try:
                print()  # Blank line for clarity
                msgs = self.get_unread()  # Get unread messages method
                while msgs is None:  # Listen for unread messages loop
                    time.sleep(self.check_timer)
                    msgs = self.get_unread()
                for msg_id in msgs.keys():
                    if type(msg_id) is not int:  # Check if key message is integer or not
                        continue
                    self.parse_msg(msgs, msg_id)  # If it is integer than parse message and send sms

            except KeyboardInterrupt:
                self.imap_client.logout()  # Safe logout on keyboard interruption
                break
            except OSError:
                continue
            finally:
                self.imap_client.logout()  # When job is done safe logout


    def get_unread(self):
        """
        Fetch unread emails
        """
        uids = self.imap_client.search(['UNSEEN'])  # Unseen id's
        if not uids:
            return None
        else:
            print("Found %s unreads" % len(uids))
            return self.imap_client.fetch(uids, ['BODY[]', 'FLAGS'])  # Return unseen messages
    
    def imap_init(self):
        """
        Initialize IMAP connection
        """
        print("Initializing IMAP... ", end='')
        # Create imap client
        self.imap_client = imapclient.IMAPClient(os.getenv("IMAPSERVER"))
        # Login to imap client
        self.imap_client.login(self.my_email, self.pwd)
        # Select inbox folder
        self.imap_client.select_folder("INBOX")
        print("Done. ")
    
    def parse_msg(self, raws, a):
        """
        Parse message and send sms with twilio
        """
        print("Parsing message with uid " + str(a))
        # Using pyzmail to get the message body (3rd party module)
        msg = pyzmail.PyzMessage.factory(raws[a][b'BODY[]'])
        # Using var frm as from is python reserved word
        msg_from = msg.get_addresses('from')
        if msg_from[0][1] not in self.wait_for_email:
            print("Unread is from %s <%s> skipping" % (msg_from[0][0],
                                                       msg_from[0][1]))
            return None

        if msg.text_part is None:
            print("No text part, cannot parse")
            return None
        text = msg.text_part.get_payload().decode(msg.text_part.charset)  # pyzmail method to decode

        ################## FOR TWILIO SMS ########################
        for allowed_email in self.wait_for_email:
            if allowed_email in msg_from[0]:
                """
                Enter twilio credentials
                """
                account_sid = os.getenv('account_sid')
                auth_token = os.getenv('auth_token')
                my_cell = os.getenv('my_cell')
                my_twilio_phone = os.getenv('my_twilio_phone')
                client = Client(account_sid, auth_token)  # Client imported from twilio.rest
                if len(text) > 100:
                    text = text[:100] + "..."
                my_msg = 'From: {}\nSubject: {}\nMessage: {}'.format(allowed_email, msg.get_subject(), text)  # Format message body for sms
                print(my_msg)
                client.messages.create(to=my_cell, from_=my_twilio_phone, body=my_msg)
                print('SMS is sent.')
                return


if __name__ == '__main__':
    listener = MailListener()  # Create instance of Mail Listener
    listener.run()  # Run instance
