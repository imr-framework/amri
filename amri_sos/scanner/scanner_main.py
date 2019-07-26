if __name__ == '__main__':
    import sys
    import os

    script_path = os.path.abspath(__file__)
    SEARCH_PATH = script_path[:script_path.index('amri-sos') + len('amri-sos') + 1]
    sys.path.insert(0, SEARCH_PATH)

import os
import shutil
import time
import uuid

from amri_sos.scanner import scanner_ui_main as scanner_ui_main
from amri_sos.utils import constants
from pathlib import Path
from amri_sos.utils import utils
from amri_sos.utils.log_utils import log
from amri_sos.utils.sitrep_offline import Sitrep_offline
from pulseq.core.Sequence.sequence import Sequence

FILE_CHECK_INTERVAL = constants.FILE_CHECK_INTERVAL

SCANNER_SEQ_WAIT_EXTRA = 30

WIN_EXTERNAL_SEQ_SRC_PATH = constants.WIN_EXTERNAL_SEQ_SRC_PATH
WIN_EXTERNAL_SEQ_DEST_PATH = constants.WIN_EXTERNAL_SEQ_DEST_PATH

WIN_SCAN_JOB_PATH = constants.WIN_SCAN_JOB_PATH
WIN_RAW_FILES_PATH = constants.WIN_RAW_FILES_PATH


def __get_latest_dat_file():
    # Copy latest acquired data (by file modification time) to Z:/AMRI/raw
    SEARCH_PATH = Path('C:/TEMP')
    files, file_mtimes = SEARCH_PATH.glob('*.*'), []
    # Filter relevant files only
    files = list(filter(lambda file: file.startswith('meas') and 'pulseq' in file and file.endswith('.dat'), files))

    # Retrieve modification times for files
    for f in files:
        mtime = os.path.getmtime(SEARCH_PATH / f)
        file_mtimes.append(mtime)

    sorted_file_mtimes = sorted(file_mtimes, reverse=True)
    latest_file = files[file_mtimes.index(sorted_file_mtimes[0])]
    latest_file_full_path = SEARCH_PATH / latest_file
    log('File found: {}'.format(latest_file_full_path))

    return latest_file, str(latest_file_full_path)


def __get_seq_exec_time():
    """Return execution time of external.seq"""
    s = Sequence()
    s.read(WIN_EXTERNAL_SEQ_DEST_PATH)
    d, _, _, = s.duration()
    d = d[0]

    return d


# Wait for offline Sitrep file to be created
log('Waiting for Sitrep...')
while WIN_SCAN_JOB_PATH.exists() is False:
    time.sleep(FILE_CHECK_INTERVAL)

sitrep_offline = Sitrep_offline()

# Copy raw data file from C:/TEMP to Z:/AMRI/raw
log('\n\nWaiting for scan job...')

# ---------
# MRI Exam
# ---------
num_scans = 1
for scan_number in range(1, num_scans + 1):
    start_scan = sitrep_offline.get_from_sitrep(key='start_scan', verbose=False)
    while start_scan is False:
        start_scan = sitrep_offline.get_from_sitrep(key='start_scan', verbose=False)
        time.sleep(FILE_CHECK_INTERVAL)
    log('Scan job found...')

    # Copy external.seq from seq_repo folder on cloud to scanner console, and compute scan_number time
    log('Copying external.seq from cloud to local...')
    shutil.copy2(str(WIN_EXTERNAL_SEQ_SRC_PATH), str(WIN_EXTERNAL_SEQ_DEST_PATH))
    seq_scan_time = __get_seq_exec_time() + SCANNER_SEQ_WAIT_EXTRA

    log('Waiting {} seconds (estimated) for scan to finish...'.format(seq_scan_time))
    scan_job = [str(uuid.uuid4().int), utils.get_25y_from_now(), 'Other', '180', '180']
    scanner_ui_main.main(scan_job=scan_job, seq_scan_time=seq_scan_time)

    # Copy raw data file from C:/TEMP to Z:/AMRI/raw
    log('Copying relevant acquired file to cloud...')
    latest_file, latest_file_full_path = __get_latest_dat_file()
    shutil.copy2(latest_file_full_path, str(WIN_RAW_FILES_PATH / latest_file))
    # Rename raw file to scan.dat
    os.rename(WIN_RAW_FILES_PATH / latest_file, WIN_RAW_FILES_PATH / 'scan.dat')
    os.remove(latest_file_full_path)  # Remove file from C:\TEMP

log('Scan has ended.')
