from __future__ import print_function

import base64
import os.path
import pickle
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from amri_sos.utils import constants
from amri_sos.utils.log_utils import log

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

SECRETS_PATH = constants.SECRETS_PATH


def __create_message(send_to):
    """Create a message for an email.

    Parameters
    ----------
      to : str
        Email address of the receiver.

    Returns
    -------
    raw_dict : dict
        A dict object containing a base64url encoded email object.
    """
    share_link = 'https://drive.google.com/open?id=1qwKZIHgexuj9J8DWvYzJKVvr8IX-cWbQ'
    message_text = """
    Dear User,
    
    Raw data (.mat and .npy files) for your scan are available on this Google Drive folder: {}""".format(share_link)
    message = MIMEText(message_text)
    message['to'] = send_to
    message['from'] = 'imr.framework2018@gmail.com'
    message['subject'] = 'AMRI-SOS: Raw data available notification'
    b64_bytes = base64.urlsafe_b64encode(message.as_bytes())
    b64_string = b64_bytes.decode()
    raw_dict = {'raw': b64_string}
    return raw_dict


def __build_service():
    """
    Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_path = SECRETS_PATH / 'gmail_token.pickle'
    if token_path.exists():
        with open(str(token_path), 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(SECRETS_PATH / 'client_secret_gmail.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open(str(token_path), 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


def notify_user(send_to):
    """
    Send an email message.

    Parameters:
    -----------
    send_to : str
        Recipient's email address
    """

    service = __build_service()
    message_raw = __create_message(send_to=send_to)
    (service.users().messages().send(userId='me', body=message_raw).execute())
    log('Email successfully sent to {}'.format(send_to))
