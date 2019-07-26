from pathlib import Path

FILE_CHECK_INTERVAL = 1

# Secrets
SECRETS_PATH = Path(__file__).parent / 'secrets'

# scan_job.txt
MAC_SCAN_JOB_PATH = Path('/data/AMRI/sitrep_offline.txt')
WIN_SCAN_JOB_PATH = Path('Z:/AMRI/sitrep_offline.txt')

# Raw data
MAC_RAW_FILES_PATH = Path('/data/AMRI/raw/')
WIN_RAW_FILES_PATH = Path('Z:/AMRI/raw/')

# external.seq
MAC_EXTERNAL_SEQ_REPO_PATH = Path('/data/AMRI/seq_repo/')
# TODO Switch path below for release
# MAC_EXTERNAL_SEQ_REPO_PATH = Path('/Users/sravan953/Desktop/')
WIN_EXTERNAL_SEQ_SRC_PATH = Path('Z:/AMRI/seq_repo/external.seq')
WIN_EXTERNAL_SEQ_DEST_PATH = Path('C:/Medcom/MriCustomer/seq/pulseq/external.seq')

# AMRI SOS Google Drive
SEQ_RESPONSES_FOLDER_ID = '0B7vXgLdDs0yxfjRDTDlIbkVXNjNRQWN3dzJDZ2dJczZueEhJVl9JTXh5TVdXNzNNQXlPQTQ'
RAWDATA_FOLDER_ID = '1qwKZIHgexuj9J8DWvYzJKVvr8IX-cWbQ'

# AMRI SOS Google Sheets
RESPONSES_SPREADSHEET_ID = '1s-VM5tBg1AONUx-3ng0iYU1ztMdRlsfZHC7pQgwCMeA'
TIMESTAMP_RANGE_NAME = 'Form Responses 2!A1:A'
EMAIL_RANGE_NAME = 'Form Responses 2!B1:B'
FILENAME_RANGE_NAME = 'Form Responses 2!G1:G'
COMPLETED_RANGE_NAME = 'Form Responses 2!I1:I'
