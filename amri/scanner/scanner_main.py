if __name__ == '__main__':
    import sys
    from pathlib import Path

    SEARCH_PATH = Path(__file__).parent.parent.parent
    sys.path.insert(0, SEARCH_PATH)

import os
import shutil
import time

from amri.scanner import scanner_ui_main as scanner_ui_main
from amri.scanner import scanner_ui_repeat as scanner_ui_repeat
from amri.utils import constants
from amri.utils import crypt_utils
from amri.utils.json_utils import JsonUtils
from amri.utils.log_utils import log
from amri.utils.sitrep_offline import Sitrep_offline

FILE_CHECK_INTERVAL = constants.FILE_CHECK_INTERVAL

SCANNER_SEQ_WAIT_EXTRA = 30

WIN_EXTERNAL_SEQ_SRC_PATH = constants.WIN_EXTERNAL_SEQ_SRC_PATH
WIN_EXTERNAL_SEQ_DEST_PATH = constants.WIN_EXTERNAL_SEQ_DEST_PATH

WIN_SCAN_JOB_PATH = constants.WIN_SCAN_JOB_PATH
WIN_RAW_FILES_PATH = constants.WIN_RAW_FILES_PATH


def __get_latest_dat_file():
    # Copy latest acquired data (by file modification time) to Z:/AMRI/raw
    SEARCH_PATH = 'C:/TEMP'
    files, file_mtimes = os.listdir(SEARCH_PATH), []
    # Filter relevant files only
    files = list(filter(lambda file: file.startswith('meas') and 'pulseq' in file and file.endswith('.dat'), files))

    # Retrieve modification times for files
    for f in files:
        mtime = os.path.getmtime(os.path.join(SEARCH_PATH, f))
        file_mtimes.append(mtime)

    sorted_file_mtimes = sorted(file_mtimes, reverse=True)
    latest_file = files[file_mtimes.index(sorted_file_mtimes[0])]
    latest_file_full_path = os.path.join(SEARCH_PATH, latest_file)
    log('File found: {}'.format(latest_file_full_path))

    return latest_file, latest_file_full_path


# def __inline_recon():
#     """Perform dat2py on the file in C:/TEMP"""
#     log('Proceeding to perform inline reconstruction...')
#     latest_file, latest_file_full_path = __get_latest_dat_file()
#
#     # Retrieve image space data and plot
#     _, image_space = dat2py.main(latest_file_full_path)
#     dat2py.plot_image_data(image_space)


def __get_seq_exec_time():
    """Return execution time of external.seq"""
    f = open(WIN_EXTERNAL_SEQ_DEST_PATH, 'r')
    while not '# AMRI' in f.readline():
        pass
    f.readline()  # te
    tr = float(f.readline().split('tr=')[1])
    f.readline()  # flip90
    Ny = int(f.readline().split('Ny=')[1])
    slices = int(f.readline().split('slices=')[1])
    nsa = int(f.readline().split('nsa=')[1])
    f.close()
    return int(Ny * tr * slices * nsa)


# Wait for offline Sitrep file to be created
log('Waiting for Sitrep...')
while os.path.exists(WIN_SCAN_JOB_PATH) is False:
    time.sleep(FILE_CHECK_INTERVAL)

sitrep_offline = Sitrep_offline()
json_obj = JsonUtils()

# ---------
# ISP
# ---------
log('\n\nWaiting for ISP job...')
start_isp = sitrep_offline.get_from_sitrep(key='start_isp', nested_in='isp', verbose=False)
while start_isp is False:
    start_isp = sitrep_offline.get_from_sitrep(key='start_isp', nested_in='isp', verbose=False)
    time.sleep(FILE_CHECK_INTERVAL)

log('Performing ISP... ')
crypt_key = sitrep_offline.get_from_sitrep(key='crypt_key', verbose=False)
patient_info_json_str_encrypted = sitrep_offline.get_from_sitrep(key='patient_info', verbose=False)
patient_info_json_str = crypt_utils.decrypt(crypt_key, patient_info_json_str_encrypted)
patient_info_dict = json_obj.make_dict_from_json_str(patient_info_json_str)
scan_job = [patient_info_dict['uuid'], patient_info_dict['dob'], patient_info_dict['gender'],
            patient_info_dict['height_cms'], patient_info_dict['weight_lbs']]
shutil.copy2(WIN_EXTERNAL_SEQ_SRC_PATH, WIN_EXTERNAL_SEQ_DEST_PATH)
seq_scan_time = __get_seq_exec_time() + SCANNER_SEQ_WAIT_EXTRA
log('Waiting {} seconds (estimated) for ISP to finish...'.format(seq_scan_time))
# NOTE: scanner_ui_main will wait for scan_number to finish
pulseq_left, pulseq_top = scanner_ui_main.main(scan_job=scan_job, seq_scan_time=seq_scan_time)
log('ISP done.')

# Copy raw data file from C:/TEMP to Z:/AMRI/raw
log('\n\nWaiting for first scan job...')
latest_file, latest_file_full_path = __get_latest_dat_file()
shutil.copy2(latest_file_full_path, WIN_RAW_FILES_PATH + latest_file)
os.rename(WIN_RAW_FILES_PATH + latest_file, WIN_RAW_FILES_PATH + 'isp.dat')  # Rename raw file to isp.dat
os.remove(latest_file_full_path)  # Remove file from C:\TEMP

# ---------
# MRI Exam
# ---------
num_scans = 3
for scan_number in range(1, num_scans + 1):
    start_scan = sitrep_offline.get_from_sitrep(key='start_scan{}'.format(scan_number),
                                                nested_in='scan{}'.format(scan_number), verbose=False)
    while start_scan is False:
        start_scan = sitrep_offline.get_from_sitrep(key='start_scan{}'.format(scan_number),
                                                    nested_in='scan{}'.format(scan_number), verbose=False)
        time.sleep(FILE_CHECK_INTERVAL)
    log('Scan job {} found...'.format(scan_number))

    # Copy external.seq from seq_repo folder on cloud to scanner console, and compute scan_number time
    log('Copying external.seq from cloud to local...')
    shutil.copy2(WIN_EXTERNAL_SEQ_SRC_PATH, WIN_EXTERNAL_SEQ_DEST_PATH)
    seq_scan_time = __get_seq_exec_time() + SCANNER_SEQ_WAIT_EXTRA

    log('Waiting {} seconds (estimated) for scan to finish...'.format(seq_scan_time))
    # NOTE: scanner_ui_repeat will wait for scan_number to finish
    scanner_ui_repeat.main(seq_scan_time=seq_scan_time, pulseq_left=pulseq_left, pulseq_top=pulseq_top)

    # Copy raw data file from C:/TEMP to Z:/AMRI/raw
    log('Copying relevant acquired file to cloud...')
    latest_file, latest_file_full_path = __get_latest_dat_file()
    shutil.copy2(latest_file_full_path, WIN_RAW_FILES_PATH + latest_file)
    # Rename raw file to scan_x.dat
    os.rename(WIN_RAW_FILES_PATH + latest_file, WIN_RAW_FILES_PATH + 'scan{}.dat'.format(scan_number))
    os.remove(latest_file_full_path)  # Remove file from C:\TEMP

    if scan_number != num_scans:
        log('Waiting for next scan job...\n\n')
    # threading.Thread(target=__inline_recon()).start()
