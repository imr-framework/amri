import datetime
import os
import time
import uuid

import amri.utils.constants as utils_constants
from amri.usernode.google_stt import google_stt
from amri.usernode.google_tts import google_tts
from amri.utils.log_utils import log

audio_file_path = os.path.dirname(os.path.abspath(__file__))
audio_file_path = os.path.normpath(os.path.join(audio_file_path, 'output.mp3'))


def main():
    """
    Returns:
    --------
    subject_info : list
        List of subject parameter information; first entry in the list is timestamp
    """
    # Initialize Google TTS and Google STT
    google_stt_obj = google_stt()
    google_tts_obj = google_tts()

    text = 'Welcome, let us proceed to register the subject.'
    log(text)
    google_tts_obj.speak(text)

    text = '\nWhat is the subject\'s last name?'
    log(text)
    google_tts_obj.speak(text)
    last_name = google_stt_obj.listen()

    text = '\nWhat is the subject\'s gender?'
    log(text)
    google_tts_obj.speak(text)
    while True:
        gender = google_stt_obj.listen()
        gender = 'male' if gender == 'mail' else gender
        gender = 'male' if gender == 'men' else gender
        if gender != 'male' and gender != 'female' and gender != 'other':
            text = 'Sorry, I couldn\'t understand that, let us try again. What is the subject\'s gender?'
            google_tts_obj.speak(text)
        else:
            break

    text = '\nWhat is the subject\'s age?'
    log(text)
    google_tts_obj.speak(text)
    while True:
        age = google_stt_obj.listen()
        if not age.isnumeric() or int(age) > 100 or int(age) < 1:
            text = 'Sorry, I couldn\'t understand that, let us try again. What is the subject\'s age?'
            google_tts_obj.speak(text)
        else:
            break
    current_year = datetime.datetime.now().year
    dob = '1/1/{}'.format(current_year - int(age))

    text = '\nWhat is the subject\'s height in centimeters?'
    log(text)
    google_tts_obj.speak(text)
    while True:
        height_cms = google_stt_obj.listen()
        if not height_cms.isnumeric() or int(height_cms) < 121 or int(height_cms) > 213:
            text = 'Sorry, I couldn\'t understand that, let us try again. What is the subject\'s height in centimeters?'
            google_tts_obj.speak(text)
        else:
            break

    text = '\nWhat is the subject\'s weight in pounds?'
    log(text)
    google_tts_obj.speak(text)
    while True:
        weight_lbs = google_stt_obj.listen()
        if not weight_lbs.isnumeric() or int(weight_lbs) < 88 or int(weight_lbs) > 286:
            text = 'Sorry, I couldn\'t understand that, let us try again. What is the subject\'s weight in pounds?'
            google_tts_obj.speak(text)
        else:
            break

    text = '\nAlright. Now, please state your application.'
    log(text)
    google_tts_obj.speak(text)
    application = google_stt_obj.listen()

    text = '\nHow many minutes would you like to spend on this exam?'
    log(text)
    google_tts_obj.speak(text)
    while True:
        time_mins = google_stt_obj.listen()
        if ' ' in time_mins:
            time_mins = time_mins.split(' ')[0]
        if time_mins.isalpha() or float(time_mins) < 0:
            text = 'Sorry, I couldn\'t understand that, let us try again. How many minutes would you like to spend on ' \
                   'this exam?'
            google_tts_obj.speak(text)
        else:
            time_mins = float(time_mins)
            break
    time_seconds = int(time_mins * 60)

    text = '\nThank you, we will begin momentarily...'
    log(text)
    google_tts_obj.speak(text)

    os.remove(audio_file_path)

    patient_uuid = str(uuid.uuid4().int)
    patient_info = [time.time(), last_name, patient_uuid, dob, gender, height_cms, weight_lbs, application,
                    time_seconds]
    patient_info = dict(zip(utils_constants.PATIENT_PARAMS_KEYS, patient_info))

    del google_tts_obj
    return patient_info
