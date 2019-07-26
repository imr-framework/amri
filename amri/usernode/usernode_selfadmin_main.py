if __name__ == '__main__':
    import sys
    import os

    script_path = os.path.abspath(__file__)
    SEARCH_PATH = script_path[:script_path.index('imr-framework') + len('imr-framework') + 1]
    sys.path.insert(0, SEARCH_PATH)

import threading
import time

from amri.usernode import voice_activation_selfadmin_main
from amri.usernode import voice_activation_update_time
from amri.usernode.google_tts import google_tts
from amri.utils import constants
from amri.utils import crypt_utils
from amri.utils.json_utils import JsonUtils
from amri.utils.log_utils import log
from amri.utils.pydrive_utils import PyDriveUtils
from amri.utils.sitrep import Sitrep

PATIENT_PARAMS_KEYS = constants.PATIENT_PARAMS_KEYS
CONTRASTS = constants.CONTRASTS
FILE_CHECK_INTERVAL = constants.FILE_CHECK_INTERVAL

pydrive = PyDriveUtils()
sitrep = Sitrep()
json_obj = JsonUtils()
google_tts_obj = google_tts()


def __request_crypt_key_async():
    global crypt_key
    sitrep.put_in_sitrep(key='crypt_key_request', value=True, verbose=False)  # Request crypt key
    time.sleep(FILE_CHECK_INTERVAL)

    crypt_key = False
    while crypt_key is False:  # Retrieve crypt key
        crypt_key = sitrep.get_from_sitrep(key='crypt_key', verbose=False)
        time.sleep(FILE_CHECK_INTERVAL)
    return crypt_key


def __get_seq_scan_time(scan_number):
    # Retrieve wait time for current scan_number
    seq_scan_time = False
    while seq_scan_time is False:
        seq_scan_time = sitrep.get_from_sitrep(key='scan{}_wait_seconds'.format(scan_number),
                                               nested_in='scan{}'.format(scan_number), verbose=False)
        time.sleep(FILE_CHECK_INTERVAL)
    return seq_scan_time


def __is_scan_result_available(scan_number):
    # Determine number of slices
    multislice = False
    while multislice is False:
        multislice = sitrep.get_from_sitrep(key='scan{}_num_slices'.format(scan_number),
                                            nested_in='scan{}'.format(scan_number), verbose=False)
        time.sleep(FILE_CHECK_INTERVAL)

    # Are all slices available online?
    scan_result = False
    while scan_result is False:
        if multislice > 1:
            scan_result = sitrep.get_from_sitrep(
                key='scan{}_slice{}_available'.format(scan_number, multislice),
                nested_in='scan{}'.format(scan_number),
                verbose=False)
        else:
            scan_result = sitrep.get_from_sitrep(key='scan{}_available'.format(scan_number),
                                                 nested_in='scan{}'.format(scan_number), verbose=False)
        time.sleep(FILE_CHECK_INTERVAL)
    return True, multislice


# Run encryption key request on deg separate thread so that we can be ready to encrypt patient_info_dict once it comes in
request_crypt_key_thread = threading.Thread(target=__request_crypt_key_async)
request_crypt_key_thread.start()

# ---------
# PATIENT REGISTRATION
# ---------
# Initiate voice interaction flow, retrieve patient parameters and encrypt it
patient_info_dict = voice_activation_selfadmin_main.main()
# import uuid
# from pygame import mixer
#
# patient_info_dict = str(time.time()) + '\nTest\n'
# patient_info_dict += str(uuid.uuid4().int)
# patient_info_dict += '\n01/01/1980\nmale\n180\n180\nbrain screen protocol\n150'
# patient_info_dict = patient_info_dict.split('\n')
# patient_info_dict = dict(zip(PATIENT_PARAMS_KEYS, patient_info_dict))
# mixer.init()
patient_info_json_str = json_obj.make_json_str_from_dict(patient_info_dict)

# Wait for crypt key to be retrieved, if it has not already been retrieved
log('Waiting for encryption key from the cloud...')
request_crypt_key_thread.join()

# Encrypt patient parameters
log('Encrypting patient information...')
patient_info_json_str_encrypted = crypt_utils.encrypt(key=crypt_key, msg=patient_info_json_str)

# Upload encrypted patient parameters to cloud
text = 'Uploading encrypted patient information to the cloud...'
log(text)
google_tts_obj.speak(text)
sitrep.put_in_sitrep(key='patient_info', value=patient_info_json_str_encrypted, verbose=False)

# ---------
# ISP
# ---------
isp_wait_time = False
while isp_wait_time is False:  # Check if ISP has started
    isp_wait_time = sitrep.get_from_sitrep('isp_wait_seconds', nested_in='isp', verbose=False)
    time.sleep(FILE_CHECK_INTERVAL)

# Inform user of ISP to
text = 'Please wait an estimated {} seconds while intelligent slice planning is performed...'.format(isp_wait_time)
log(text)
google_tts_obj.speak(text)

# Is exam valid? (all sequences went through?)
while True:
    exam_valid = sitrep.get_from_sitrep(key='exam_valid', verbose=False)
    if exam_valid is True:
        text = 'Alright, looks like we can proceed with the scan...'
        log(text)
        google_tts_obj.speak(text)
        break
    elif not isinstance(exam_valid, bool):
        issue = exam_valid
        if 'time_acq_' in issue:
            time_seconds_old = int(patient_info_dict['time_seconds'])
            time_seconds_new = int(issue.split('time_acq_')[1])
            proceed = voice_activation_update_time.main(time_seconds_old=time_seconds_old,
                                                        time_seconds_new=time_seconds_new)

            if proceed:
                sitrep.remove_from_sitrep(key='issue', verbose=False)
                patient_info_dict['time_seconds'] = time_seconds_new
                patient_info_json_str = json_obj.make_json_str_from_dict(patient_info_dict)
                patient_info_json_str_encrypted = crypt_utils.encrypt(key=crypt_key, msg=patient_info_json_str)
                sitrep.put_in_sitrep(key='patient_info', value=patient_info_json_str_encrypted, verbose=False)
                sitrep.put_in_sitrep(key='issue_response', value=True, verbose=False)
            else:
                text = 'Alright, that will be all. Thank you.'
                log(text)
                google_tts_obj.speak(text)
                sitrep.put_in_sitrep(key='issue_response', value=-1, verbose=False)
                exit(code=0)
    time.sleep(FILE_CHECK_INTERVAL)

# ---------
# MRI EXAM
# ---------
num_scans = 3
for scan_number in range(1, num_scans + 1):
    start_scan = False
    while start_scan is False:
        start_scan = sitrep.get_from_sitrep(key='start_scan{}'.format(scan_number),
                                            nested_in='scan{}'.format(scan_number), verbose=False)

        if scan_number != 1:
            if isinstance(start_scan, str) and 'time_acq_' in start_scan:  # Could be time acq issue for scan 2 and 3
                time_seconds_new = start_scan.split('time_acq_')[1]
                sitrep.remove_from_sitrep(key='issue', verbose=False)
                text = 'The noise level in the previous acquisition has resulted in longer scan times for the current ' \
                       'sequence: {}'.format(time_seconds_new)
                log('\n' + text)
                google_tts_obj.speak(text)
        time.sleep(FILE_CHECK_INTERVAL)

    text = 'Scan {} of {} in progress, {}...'.format(scan_number, num_scans, CONTRASTS[scan_number - 1])
    log('\n\n' + text)
    google_tts_obj.speak(text)

    seq_scan_time = __get_seq_scan_time(scan_number)

    text = 'Waiting an estimated {} seconds for data from scan {}...'.format(seq_scan_time, scan_number)
    log(text)
    google_tts_obj.speak(text)
    time.sleep(seq_scan_time)

    # Determine number of slices in this scan_number
    scan_available, multislice = __is_scan_result_available(scan_number=scan_number)

    text = 'Retrieving data for scan {}...'.format(scan_number)
    log(text)
    google_tts_obj.speak(text)

    if scan_available:
        if multislice:
            for sli in range(multislice):
                # sli is zero-indexed, but scan_number is not
                filename = 'scan{}_slice{}.tiff'.format(scan_number, sli + 1)
                files = pydrive.search_for_files(filename)
                for f in files:
                    if filename in f['title']:
                        f.GetContentFile(f['title'])
                        image_path = os.path.dirname(os.path.abspath(__file__))
                        os.system('open ' + os.path.join(image_path, f['title']))
        else:
            filename = 'scan{}.tiff'.format(scan_number)
            files = pydrive.search_for_files(filename)
            for f in files:
                if filename in f['title']:
                    f.GetContentFile(f['title'])
                    image_path = os.path.dirname(os.path.abspath(__file__))
                    os.system('open ' + os.path.join(image_path, f['title']))

text = 'That will be all, thank you.'
log(text)
google_tts_obj.speak(text)
