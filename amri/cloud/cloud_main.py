if __name__ == '__main__':
    import sys
    from pathlib import Path

    SEARCH_PATH = Path(__file__).parent.parent.parent
    sys.path.insert(0, SEARCH_PATH)

import time

import numpy as np
from PIL import Image
from scipy.misc import imrotate

import amri.dat2py.dat2py_main as dat2py
import amri.cloud.lut.lut as lut
from amri.cloud.isp import tf_elm_load_model
from amri.utils import constants
from amri.utils import crypt_utils
from amri.utils.dbutils import DbUtils
from amri.utils.json_utils import JsonUtils
from amri.utils.log_utils import log
from amri.utils.make_isp_gre import make_isp_gre
from amri.utils.pydrive_utils import PyDriveUtils
from amri.utils.sitrep import Sitrep

FILE_CHECK_INTERVAL = constants.FILE_CHECK_INTERVAL

CLOUD_SEQ_WAIT_EXTRA = 5
USERNODE_SEQ_WAIT_EXTRA = 5

MAC_EXTERNAL_SEQ_REPO_PATH = constants.MAC_EXTERNAL_SEQ_REPO_PATH
MAC_RAW_FILES_PATH = constants.MAC_RAW_FILES_PATH
MAC_SCAN_JOB_PATH = constants.MAC_SCAN_JOB_PATH


def __is_raw_file_relevant(file, target_filename):
    return target_filename in file and file.endswith('.dat')


def __get_seq_exec_time():
    """Return execution time of external.seq"""
    f = open(MAC_EXTERNAL_SEQ_REPO_PATH + 'external.seq', 'r')
    while not '# AMRI' in f.readline():
        pass
    f.readline()  # te
    tr = float(f.readline().split('tr=')[1])
    f.readline()  # flip90
    Ny = int(f.readline().split('Ny=')[1])
    slices = int(f.readline().split('slices=')[1])
    nsa = int(f.readline().split('nsa=')[1])
    f.close()
    return round(Ny * tr * slices * nsa, 3)


# ---------
# INITIAL CLEANUP
# ---------
if os.path.exists(MAC_SCAN_JOB_PATH):  # Remove offline scan job
    os.remove(MAC_SCAN_JOB_PATH)
if os.path.isdir(MAC_RAW_FILES_PATH):  # Remove raw files
    files = os.listdir(MAC_RAW_FILES_PATH)
    for f in files:
        os.remove(os.path.join(MAC_RAW_FILES_PATH, f))

pydrive = PyDriveUtils()
sitrep = Sitrep()
json_obj = JsonUtils()

# ---------
# PATIENT REGISTRATION
# ---------
log('Waiting for encryption key request from user node...')  # Cryp
request = False
while request is False:
    request = sitrep.get_from_sitrep(key='crypt_key_request', verbose=False)
    time.sleep(FILE_CHECK_INTERVAL)

# Upload encryption key
log('Uploading encryption key...', endline=' ')
crypt_key = crypt_utils.gen_crypt_key().decode('utf-8')
sitrep.put_in_sitrep(key='crypt_key', value=crypt_key, verbose=False)
log('Done.')

# Retrieve encrypted patient information
log('Waiting for user node activation...')
patient_info_json_str_encrypted = False
while patient_info_json_str_encrypted is False:
    patient_info_json_str_encrypted = sitrep.get_from_sitrep(key='patient_info', verbose=False)
    time.sleep(FILE_CHECK_INTERVAL)

# Decrypt patient parameters to determine time to be spent on exam
patient_info_json_str = crypt_utils.decrypt(crypt_key, patient_info_json_str_encrypted)
patient_info_dict = json_obj.make_dict_from_json_str(patient_info_json_str)
time_seconds_remaining = int(patient_info_dict['time_seconds'])  # Retrieve time to spend on this exam

# ---------
# ISP
# ---------
# Create seq file and update Sitrep with ISP job
log('\n\nCreating ISP job...')
# isp_seq = make_t1_mprage.make_t1_mprage(te=6.5e-3, tr=13e-3, flip_deg=12, Nx=32, Ny=32, n_slices=1)
isp_seq = make_isp_gre(te=8e-3, tr=15e-3, flip_deg=56.7, Nx=32, Ny=32, n_slices=1)
isp_seq.write(os.path.join(MAC_EXTERNAL_SEQ_REPO_PATH, 'external.seq'))
sitrep.put_in_sitrep(key='start_isp', value=True, nest_in='isp', verbose=False)  # Scan job
seq_scan_time = __get_seq_exec_time()
sitrep.put_in_sitrep(key='isp_wait_seconds', value=seq_scan_time + USERNODE_SEQ_WAIT_EXTRA, nest_in='isp',
                     verbose=False)  # Inform user

log('Waiting an estimated {} seconds for ISP...'.format(seq_scan_time + CLOUD_SEQ_WAIT_EXTRA))
time.sleep(seq_scan_time + CLOUD_SEQ_WAIT_EXTRA)  # Wait for ISP to finish

while True:  # Check if ISP raw data is available
    files = list(
        filter(lambda x: __is_raw_file_relevant(file=x, target_filename='isp'), os.listdir(MAC_RAW_FILES_PATH)))
    if len(files) == 1:
        break
    time.sleep(FILE_CHECK_INTERVAL)

# Recon ISP raw file
raw_file_full_path = os.path.join(MAC_RAW_FILES_PATH, files[0])
time.sleep(5)  # TODO Debug why?
os.system('echo m1rcdsi2012 | sudo -S chmod 777 ' + raw_file_full_path)  # Set appropriate permissions
_, image_space = dat2py.main(dat_file_path=raw_file_full_path)
sos = dat2py.get_image(image_space=image_space)
sos = imrotate(sos, angle=0)  # Rotate by 0 because imrotate scales image to 0-255
slice_offset = tf_elm_load_model.main(sos)  # Feed forward on restored ELM model to get RF slice offset
slice_offset = (31 - slice_offset) * 5
log('Slice offset: {}'.format(slice_offset))

# ---------
# LUT
# ---------
lut_obj = lut.LUT()
lut_obj.rf_offset = slice_offset
lut_obj.update_lut_from_image(image=sos, patch_size=2)  # Update LUT with noise from ISP

# ---------
# EXAM VALIDATION
# ---------
exam_valid = False
while not exam_valid:
    # Lookup LUT to check if exam can proceed based on time constraints
    seq_to_write, time_seconds_remaining_modified = lut_obj.get_last_n_sequences(
        time_seconds_remaining=time_seconds_remaining, last_n=3)
    if time_seconds_remaining_modified != time_seconds_remaining:
        log('\nAcquisition time modified, waiting for user to revert...')
        sitrep.put_in_sitrep(key='issue', value='time_acq_{}'.format(time_seconds_remaining_modified), verbose=False)

        issue_response = False  # Wait for user to revert
        while not issue_response:
            issue_response = sitrep.get_from_sitrep(key='issue_response', ignore_issue=True, verbose=False)
            time.sleep(FILE_CHECK_INTERVAL)
        log('User reverted; re-evaluating...')
        sitrep.remove_from_sitrep(key='issue_response', verbose=False)

        if issue_response:
            time_seconds_remaining = time_seconds_remaining_modified
            log('Exam valid...')
            exam_valid = True
            sitrep.put_in_sitrep(key='exam_valid', value=True, verbose=False)
            break  # TODO optimize flow
        elif issue_response == -1:
            log('User declined to proceed with modified acquisition time, quitting...')
            exit(0)
    else:
        log('Exam valid...')
        exam_valid = True
        sitrep.put_in_sitrep(key='exam_valid', value=True, verbose=False)

# ---------
# DATABASE
# ---------
db_utils_obj = DbUtils()  # Update database
db_utils_obj.add_patient_to_database(patient_info_dict)
db_utils_obj.save_database()
del db_utils_obj

# ---------
# MRI EXAM
# ---------
raw_files_archive = []  # List of raw files that have already been reconstructed, so we can skip them
num_scans = 3  # Hardcoded for now, since we are working on 3 sequences in MRI brain screen protocol
for scan_number in range(1, num_scans + 1):
    log('\nScan {}/{}...'.format(scan_number, num_scans))

    log('Writing seq file to disk...')
    seq_to_write.write(os.path.join(MAC_EXTERNAL_SEQ_REPO_PATH, 'external.seq'))

    log('Issuing scan job...')
    sitrep.put_in_sitrep(key='start_scan{}'.format(scan_number), value=True, nest_in='scan{}'.format(scan_number),
                         verbose=False)

    seq_scan_time = __get_seq_exec_time()
    log('Waiting an estimated {} seconds for raw data from scan {} ...'.format(seq_scan_time + CLOUD_SEQ_WAIT_EXTRA,
                                                                               scan_number))
    sitrep.put_in_sitrep(key='scan{}_wait_seconds'.format(scan_number), value=seq_scan_time + USERNODE_SEQ_WAIT_EXTRA,
                         nest_in='scan{}'.format(scan_number), verbose=False)
    time.sleep(seq_scan_time + CLOUD_SEQ_WAIT_EXTRA)

    # ---------
    # CHECK FOR RAW DATA
    # ---------
    while True:  # Check if raw data from this scan_number is available on this cloud
        filename = 'scan{}'.format(scan_number)
        files = list(
            filter(lambda x: __is_raw_file_relevant(file=x, target_filename=filename), os.listdir(MAC_RAW_FILES_PATH)))
        if len(files) == 1:
            break
        time.sleep(FILE_CHECK_INTERVAL)

    for raw_file in files:
        if raw_file not in raw_files_archive:  # File should not have already been reconstructed
            raw_files_archive.append(raw_file)
            # Hard coding raw_file_full_path because os.path.abspath() returns garbage like /Users/...
            raw_file_full_path = os.path.join(MAC_RAW_FILES_PATH, raw_file)
            time.sleep(5)  # TODO Debug why?
            os.system('echo m1rcdsi2012 | sudo -S chmod 777 ' + raw_file_full_path)  # Set appropriate permissions

            _, image_space = dat2py.main(dat_file_path=raw_file_full_path)
            sos = dat2py.get_image(image_space=image_space)
            sos_min = np.amin(sos)
            sos_max = np.amax(sos)
            sos = (sos - sos_min) / (sos_max - sos_min)  # Normalize

            num_slices = 1 if len(sos.shape) == 2 else sos.shape[2]
            sitrep.put_in_sitrep(key='scan{}_num_slices'.format(scan_number), value=num_slices,
                                 nest_in='scan{}'.format(scan_number), verbose=False)

            if len(sos.shape) == 3:
                for sli in range(1, num_slices + 1):
                    tiff_image = Image.fromarray(sos[:, :, sli - 1])
                    tiff_save_path = os.path.dirname(raw_file_full_path)
                    tiff_save_path = os.path.join(tiff_save_path, 'scan{}_slice{}.tiff'.format(scan_number, sli))
                    tiff_image.save(tiff_save_path, 'TIFF')
                    pydrive.upload_file(file_path=tiff_save_path,
                                        file_name='scan{}_slice{}.tiff'.format(scan_number, sli))
                    sitrep.put_in_sitrep(key='scan{}_slice{}_available'.format(scan_number, sli), value=True,
                                         nest_in='scan{}'.format(scan_number), verbose=False)
                    os.remove(tiff_save_path)
            elif len(sos.shape) == 2:
                tiff_image = Image.fromarray(sos)
                tiff_save_path = os.path.dirname(raw_file_full_path)
                tiff_save_path = os.path.join(tiff_save_path, 'scan{}.tiff'.format(scan_number))
                tiff_image.save(tiff_save_path, 'TIFF')
                pydrive.upload_file(file_path=tiff_save_path, file_name='scan{}.tiff')
                sitrep.put_in_sitrep(key='scan{}_available'.format(scan_number), value=True,
                                     nest_in='scan{}'.format(scan_number), verbose=False)

            if scan_number != 3:
                # Compute noise from reconstruction and re-init LUT
                lut_obj.update_lut_from_image(sos)

                seq_to_write, time_seconds_remaining_modified = lut_obj.get_last_n_sequences(
                    time_seconds_remaining=time_seconds_remaining, last_n=3 - scan_number)  # 1=>2,2=>1
                if time_seconds_remaining_modified != time_seconds_remaining:
                    sitrep.put_in_sitrep(key='issue', value='time_acq_{}'.format(time_seconds_remaining_modified),
                                         verbose=False)

log('\n\nExam has ended.')

# ---------
# FINAL CLEANUP
# ---------
if os.path.exists(MAC_SCAN_JOB_PATH):  # Remove offline scan job
    os.remove(MAC_SCAN_JOB_PATH)
if os.path.isdir(MAC_RAW_FILES_PATH):  # Remove raw files
    files = os.listdir(MAC_RAW_FILES_PATH)
    for f in files:
        os.remove(os.path.join(MAC_RAW_FILES_PATH, f))
