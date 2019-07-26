if __name__ == '__main__':
    import sys
    import os

    script_path = os.path.abspath(__file__)
    SEARCH_PATH = script_path[:script_path.index('amri_sos') + len('amri_sos') + 1]
    sys.path.insert(0, SEARCH_PATH)

import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from amri_sos.utils import constants

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SECRETS_PATH = constants.SECRETS_PATH

# The ID and range of a sample spreadsheet.
RESPONSES_SPREADSHEET_ID = constants.RESPONSES_SPREADSHEET_ID
TIMESTAMP_RANGE_NAME = constants.TIMESTAMP_RANGE_NAME
EMAIL_RANGE_NAME = constants.EMAIL_RANGE_NAME
FILENAME_RANGE_NAME = constants.FILENAME_RANGE_NAME
COMPLETED_RANGE_NAME = constants.COMPLETED_RANGE_NAME


def __build_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_path = SECRETS_PATH / 'sheets_token.pickle'
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(SECRETS_PATH / 'sheets_client_secret.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open(SECRETS_PATH / 'sheets_token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    return service


def __get_responses(range):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    service = __build_service()

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=RESPONSES_SPREADSHEET_ID, range=range).execute()
    values = result.get('values', [])

    if not values:
        raise Exception('No data found.')
    else:
        return values


def get_responses_email():
    return __get_responses(EMAIL_RANGE_NAME)


def get_responses_file_id():
    return __get_responses(FILENAME_RANGE_NAME)


def get_responses_completed():
    return __get_responses(COMPLETED_RANGE_NAME)


def get_responses_timestamp():
    return __get_responses(TIMESTAMP_RANGE_NAME)


def put_responses_completed(range):
    service = __build_service()
    values = [['Yes'], ]
    body = {'values': values}

    result = service.spreadsheets().values().update(spreadsheetId=RESPONSES_SPREADSHEET_ID, range=range,
                                                    valueInputOption='RAW', body=body).execute()
