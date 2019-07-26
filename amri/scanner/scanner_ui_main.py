if __name__ == '__main__':
    import sys
    import os

    script_path = os.path.abspath(__file__)
    SEARCH_PATH = script_path[:script_path.index('imr-framework') + len('imr-framework') + 1]
    sys.path.insert(0, SEARCH_PATH)

import math
import os
import subprocess
import time

import pyautogui

from amri.utils.log_utils import log

"""
1. Parse patient registration details from patient_info_dict.json and register the patient
2. Initiate scan_number
3. Wait appropriate time, retrieve the .dat file and reconstruct image 
"""

PATIENT_REGISTRATION_PYAUTOGUI_PATH = os.path.join(os.path.dirname(__file__), 'pyautogui_assets',
                                                   'patient_registration')
PATIENT_CONFIRMATION_PYAUTOGUI_PATH = os.path.join(os.path.dirname(__file__), 'pyautogui_assets',
                                                   'patient_confirmation')
PROTOCOL_PYAUTOGUI_PATH = os.path.join(os.path.dirname(__file__), 'pyautogui_assets', 'protocol')
TWIX_PYAUTOGUI_PATH = os.path.join(os.path.dirname(__file__), 'pyautogui_assets', 'twix')


def __feet_converter(number):
    temp_inch_value, feet_value = math.modf(int(number) * 0.03281)
    inch_value = temp_inch_value * 12
    return round(feet_value), round(inch_value)


def __get_to_patient_registration_page():
    log('Navigating to patient registration page...')
    # Click on 'Patient'
    pyautogui.click(10, 10)
    # Click on 'Register'
    pyautogui.click(10, 30)


def __register_patient(last_name, id, dob, gender='other', height_cms=180, weight_lbs=180):
    log('Registering patient details...')
    log('Registering last name...')
    # Enter patient's last name
    left, top = pyautogui.locateCenterOnScreen(PATIENT_REGISTRATION_PYAUTOGUI_PATH + '/patient_regis_last_name.PNG')
    pyautogui.click(left + 100, top)
    pyautogui.typewrite(last_name)

    log('Registering patient ID...')
    # Enter patient's ID
    left, top = pyautogui.locateCenterOnScreen(PATIENT_REGISTRATION_PYAUTOGUI_PATH + '/patient_regis_patient_id.PNG')
    pyautogui.click(left + 50, top)
    pyautogui.typewrite(id)

    log('Registering patient\'s DOB...')
    # Enter patient's DOB
    left, top = pyautogui.locateCenterOnScreen(PATIENT_REGISTRATION_PYAUTOGUI_PATH + '/patient_regis_dob.PNG')
    pyautogui.click(left + 100, top)
    pyautogui.typewrite(dob)

    log('Registering patient\'s gender...')
    # Enter patient's gender
    if gender.lower() == 'male':
        left, top, _, _ = pyautogui.locateOnScreen(
            PATIENT_REGISTRATION_PYAUTOGUI_PATH + '/patient_regis_male_radiobutton.PNG')
    elif gender.lower() == 'female':
        left, top, _, _ = pyautogui.locateOnScreen(
            PATIENT_REGISTRATION_PYAUTOGUI_PATH + '/patient_regis_female_radiobutton.PNG')
    else:
        left, top, _, _ = pyautogui.locateOnScreen(
            PATIENT_REGISTRATION_PYAUTOGUI_PATH + '/patient_regis_other_radiobutton.PNG')
    pyautogui.click(left, top + 5)

    log('Registering patient\'s height...')
    # Enter patient's height
    height_ft, height_inch = __feet_converter(height_cms)
    left, top = pyautogui.locateCenterOnScreen(PATIENT_REGISTRATION_PYAUTOGUI_PATH + '/patient_regis_height_ft.PNG')
    pyautogui.click(left - 50, top)
    pyautogui.typewrite(str(height_ft))
    # left, top = pyautogui.locateCenterOnScreen(PATIENT_REGISTRATION_PYAUTOGUI_PATH + '/patient_regis_height_inch.PNG')
    # pyautogui.click(left, top)
    # pyautogui.typewrite(str(height_inch))

    log('Registering patient\'s weight...')
    # Enter patient's weight
    left, top = pyautogui.locateCenterOnScreen(PATIENT_REGISTRATION_PYAUTOGUI_PATH + '/patient_regis_weight_lbs.PNG')
    pyautogui.click(left - 50, top)
    pyautogui.typewrite(str(weight_lbs))

    log('Registering patient position...')
    # Enter patient position
    left, top = pyautogui.locateCenterOnScreen(
        PATIENT_REGISTRATION_PYAUTOGUI_PATH + '/patient_regis_patient_position.PNG')
    pyautogui.click(left + 50, top)
    pyautogui.click(left + 50, top + 20)

    log('Navigating to patient confirmation page...')
    # Click Exam
    left, top = pyautogui.locateCenterOnScreen(PATIENT_REGISTRATION_PYAUTOGUI_PATH + '/patient_regis_exam.PNG')
    pyautogui.click(left, top)


def __confirm_patient():
    geethanath_coords = pyautogui.locateCenterOnScreen(
        PATIENT_CONFIRMATION_PYAUTOGUI_PATH + '/patient_conf_geethanath.PNG')
    if geethanath_coords is None:
        geethanath_coords = pyautogui.locateCenterOnScreen(
            PATIENT_CONFIRMATION_PYAUTOGUI_PATH + '/patient_conf_geethanath_2.PNG')
    if geethanath_coords is not None:
        left, top = geethanath_coords
        pyautogui.click(left, top, clicks=2)

    rapid_prototypes_coords = pyautogui.locateCenterOnScreen(
        PATIENT_CONFIRMATION_PYAUTOGUI_PATH + '/patient_conf_rapid.PNG')
    if rapid_prototypes_coords is None:
        rapid_prototypes_coords = pyautogui.locateCenterOnScreen(
            PATIENT_CONFIRMATION_PYAUTOGUI_PATH + '/patient_conf_rapid_2.PNG')
    if rapid_prototypes_coords is not None:
        left, top = rapid_prototypes_coords
        pyautogui.click(left, top, clicks=2)

    incubation_coords = pyautogui.locateCenterOnScreen(
        PATIENT_CONFIRMATION_PYAUTOGUI_PATH + '/patient_conf_incubation.PNG')
    if incubation_coords is None:
        incubation_coords = pyautogui.locateCenterOnScreen(
            PATIENT_CONFIRMATION_PYAUTOGUI_PATH + '/patient_conf_incubation_2.PNG')
    if incubation_coords is not None:
        left, top = incubation_coords
        pyautogui.click(left, top, clicks=2)
    else:
        raise Exception('Oops, something went wrong!')

    # Select body part drop down
    left, top = pyautogui.locateCenterOnScreen(PATIENT_CONFIRMATION_PYAUTOGUI_PATH + '/patient_conf_bodypart.PNG')
    pyautogui.click(left, top)

    # Select brain as bodypart
    time.sleep(0.5)
    # left, top = pyautogui.locateCenterOnScreen(PATIENT_CONFIRMATION_PYAUTOGUI_PATH + '/patient_conf_bodypart_brain.PNG')
    pyautogui.click(left, top - 125)

    # Click confirm
    left, top = pyautogui.locateCenterOnScreen(PATIENT_CONFIRMATION_PYAUTOGUI_PATH + '/patient_conf_confirm.PNG')
    pyautogui.click(left, top)

    log('Navigating to sequence page...')


def __run_protocol():
    log('Executing sequence...')
    global pulseq_left
    global pulseq_top
    time.sleep(1)
    pulseq_left, pulseq_top = pyautogui.locateCenterOnScreen(PROTOCOL_PYAUTOGUI_PATH + '/protocol_pulseq.PNG')
    # pyautogui.moveTo(left, top)
    pyautogui.click(pulseq_left, pulseq_top, clicks=2)

    time.sleep(1)
    left, top = pyautogui.locateCenterOnScreen(PROTOCOL_PYAUTOGUI_PATH + '/protocol_tick.PNG')
    pyautogui.click(left, top)

    time.sleep(1)
    left, top = pyautogui.locateCenterOnScreen(PROTOCOL_PYAUTOGUI_PATH + '/protocol_play.PNG')
    pyautogui.click(left, top)


def __copy_file_via_twix():
    """Copy acquired raw data to C:/TEMP via Twix."""
    log('Copying relevant acquired file to local via Twix...')
    # Launch Twix from command line and wait for it to open
    subprocess.Popen(['twix'])
    time.sleep(1.5)

    # Select first (most recent) file to copy
    left, top = pyautogui.locateCenterOnScreen(TWIX_PYAUTOGUI_PATH + '/twix_pulseq.PNG')
    pyautogui.rightClick(left, top + 20)
    pyautogui.click(left + 20, top + 30)

    # Confirm 'TEMP' folder as destination
    time.sleep(0.5)
    left, top = pyautogui.locateCenterOnScreen(TWIX_PYAUTOGUI_PATH + '/twix_confirm_copy.PNG')
    pyautogui.click(left, top)
    time.sleep(5)


def __close_twix():
    pyautogui.press('alt')
    pyautogui.press('f')
    pyautogui.press('x')


def main(scan_job, seq_scan_time):
    """
    Automate GUI-flow for subject registration and invoking MRI exam utilizing subject registration details parameter
    that is provided and the external.seq file found in seq_repo folder.

    Parameters:
    -----------
    scan_job : list
        List of subject registration details.
    seq_scan_time : int
        Time in millis of acquisition time of external.seq in seq_repo.

    Returns:
    --------
    pulseq_left : int
        X coordinate of left of 'pulseq' UI item on Siemens run screen.
    pulseq_top : int
        Y coordinate of top of 'pulseq' UI item on Siemens run screen.
    """

    pyautogui.PAUSE = 0.5

    patient_uuid, dob, gender, height_cms, weight_lbs = scan_job[:5]
    last_name = id = patient_uuid

    __get_to_patient_registration_page()
    __register_patient(last_name, id, dob, gender, height_cms, weight_lbs)
    __confirm_patient()

    # Run protocol and wait for it to complete execution
    __run_protocol()
    time.sleep(seq_scan_time)

    # Copy raw data via Twix to local and cloud, and close Twix
    __copy_file_via_twix()
    __close_twix()

    return pulseq_left, pulseq_top
