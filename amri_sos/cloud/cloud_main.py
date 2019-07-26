if __name__ == '__main__':
    import sys
    import os

    script_path = os.path.abspath(__file__)
    SEARCH_PATH = script_path[:script_path.index('amri-sos') + len('amri-sos') + 1]
    sys.path.insert(0, SEARCH_PATH)

import time
from argparse import ArgumentParser
from pathlib import Path

import numpy as np
from pypulseq.Sequence.sequence import Sequence
from scipy.io import savemat

import amri_sos.dat2py.dat2py_main as dat2py
from amri_sos.utils import constants
from amri_sos.utils import pygmail
from amri_sos.utils import sheets
from amri_sos.utils.log_utils import log
from amri_sos.utils.pydrive_utils import PyDriveUtils
from amri_sos.utils.sitrep_offline import Sitrep_offline

# Timing constants
FILE_CHECK_INTERVAL = constants.FILE_CHECK_INTERVAL
CLOUD_SEQ_WAIT_EXTRA = 5
USERNODE_SEQ_WAIT_EXTRA = 5

# Path constants
MAC_EXTERNAL_SEQ_REPO_PATH = constants.MAC_EXTERNAL_SEQ_REPO_PATH
MAC_RAW_FILES_PATH = constants.MAC_RAW_FILES_PATH
MAC_SCAN_JOB_PATH = constants.MAC_SCAN_JOB_PATH

# Google Drive constants
RAWDATA_FOLDER_ID = constants.RAWDATA_FOLDER_ID


def __is_raw_file_relevant(file, target_filename):
    return target_filename in file and file.endswith('.dat')


def __get_seq_exec_time():
    """Return execution time of external.seq"""
    seq = Sequence()
    seq.read(Path(MAC_EXTERNAL_SEQ_REPO_PATH) / 'external.seq')
    return seq.duration()[0]


def main(req_selection_override: bool = False):
    """
    Parameters
    ----------
    req_selection_override:bool
        Boolean flag to indicate if user will manually select requests to execute.
    """
    # ---------
    # INITIAL CLEANUP
    # ---------
    if Path(MAC_SCAN_JOB_PATH).exists():  # Remove offline scan job
        os.remove(MAC_SCAN_JOB_PATH)
    if Path(MAC_RAW_FILES_PATH).is_dir():  # Remove raw files
        files = MAC_RAW_FILES_PATH.glob('*.*')
        for f in files:
            os.remove(Path(MAC_RAW_FILES_PATH) / f)

    # ---------
    # INIT
    # ---------
    pydrive = PyDriveUtils()
    # TODO Enable sitrep_offline below for release
    sitrep_offline = Sitrep_offline()

    # ---------
    # FETCH RESPONSES
    # ---------
    responses_timestamp = sheets.get_responses_timestamp()
    responses_email = sheets.get_responses_email()
    responses_file_id = sheets.get_responses_file_id()
    responses_completed = sheets.get_responses_completed()

    first_incomplete = len(responses_completed)
    if first_incomplete == 0:  # No new .seq files to execute
        print('No new requests.')
        exit(code=0)
    response_email = responses_email[first_incomplete][0]
    response_file_id = responses_file_id[first_incomplete][0].replace('https://drive.google.com/open?id=', '')

    # ---------
    # DOWNLOAD SEQ FILE
    # ---------
    log(f'Working on request by {responses_email[first_incomplete][0]} at '
        f'{responses_timestamp[first_incomplete][0]}...')
    response_seq_bytes = pydrive.get_file_contents_as_bytes(drive_file_id=response_file_id)  # Save to disk
    response_seq_save_path = MAC_EXTERNAL_SEQ_REPO_PATH / 'external.seq'
    response_seq_save_path.write_bytes(response_seq_bytes)
    log('Done.')

    # ---------
    # MRI EXAM
    # ---------
    log('\n\nIssuing scan job...')
    # TODO Enable sitrep_offline below for release
    sitrep_offline.put_in_sitrep(key='start_scan', value=True, verbose=False)

    seq_scan_time = __get_seq_exec_time()
    log(f'Waiting an estimated {seq_scan_time + CLOUD_SEQ_WAIT_EXTRA} seconds for raw data from scan ...')
    # TODO Enable sitrep_offline below for release
    sitrep_offline.put_in_sitrep(key='scan_wait_seconds', value=seq_scan_time + USERNODE_SEQ_WAIT_EXTRA, verbose=False)
    time.sleep(seq_scan_time + CLOUD_SEQ_WAIT_EXTRA)

    # ---------
    # CHECK FOR RAW DATA
    # ---------
    while True:  # Check if raw data from this scan is available on this cloud
        filename = 'scan'
        files = list(
            filter(lambda x: __is_raw_file_relevant(file=x, target_filename=filename), os.listdir(MAC_RAW_FILES_PATH)))
        if len(files) == 1:
            break
        time.sleep(FILE_CHECK_INTERVAL)

    raw_file = files[0]
    raw_file_full_path = Path(MAC_RAW_FILES_PATH) / raw_file
    time.sleep(5)  # TODO Debug why?
    os.system('echo m1rcdsi2012 | sudo -S chmod 777 ' + raw_file_full_path)  # Set appropriate permissions

    # ---------
    # EXPORT K-SPACE AS .MAT AND .NPY
    # ---------
    log('\n\nSaving kspace as .mat and .npy...')
    k_space, _ = dat2py.main(dat_file_path=raw_file_full_path)
    export_file_name = response_seq_save_path.split('.seq')[0]
    savemat(file_name=MAC_RAW_FILES_PATH / export_file_name + '.mat', mdict={'kspace': k_space})  # Save .mat
    np.save(file=MAC_RAW_FILES_PATH + export_file_name + '.npy', arr=k_space)  # Save .npy
    log('Done.')

    # ---------
    # UPLOAD .MAT AND .NPY TO GOOGLE DRIVE
    # ---------
    log('\n\nUploading .mat and .npy files to Google Drive...')
    pydrive.upload_file(file_path=MAC_RAW_FILES_PATH + export_file_name + '.mat', child_of_folder=RAWDATA_FOLDER_ID)
    pydrive.upload_file(file_path=MAC_RAW_FILES_PATH + export_file_name + '.npy', child_of_folder=RAWDATA_FOLDER_ID)
    log('Done.')

    log('\nScan has ended.')

    # ---------
    # NOTIFY USER VIA EMAIL
    # ---------
    log(f'\nNotifying user at {response_email}')
    pygmail.notify_user(send_to=response_email)
    log('Done.')

    # ---------
    # UPDATE RESPONSE
    # ---------
    sheets.put_responses_completed(range=f'I{1 + first_incomplete}')

    # ---------
    # FINAL CLEANUP
    # ---------
    if MAC_SCAN_JOB_PATH.exists():  # Remove offline scan job
        os.remove(MAC_SCAN_JOB_PATH)
    if MAC_RAW_FILES_PATH.is_dir():  # Remove raw files
        files = MAC_RAW_FILES_PATH.glob('*.*')
        for f in files:
            os.remove(MAC_RAW_FILES_PATH / f)


if __name__ == '__main__':
    parser = ArgumentParser(description='AMRI SOS cloud service')
    parser.add_argument('-s', '--selection_override', type=bool, default=False)
    args = parser.parse_args()

    req_selection_override = args.selection_override
    main(req_selection_override=req_selection_override)
