import os

from amri.usernode.google_stt import google_stt
from amri.usernode.google_tts import google_tts
from amri.utils.log_utils import log

audio_file_path = os.path.dirname(os.path.abspath(__file__))
audio_file_path = os.path.normpath(os.path.join(audio_file_path, 'output.mp3'))


def main(time_seconds_old, time_seconds_new):
    """
    Parameters:
    -----------
    time_seconds_old : int
        Number of seconds the user originally wished to spend on the MR exam.
    time_seconds_new : int
        Number of seconds the user is suggested to spend on the MR exam.

    Returns:
    --------
    bool
        Whether the user wishes to proceed with the modified acquisition time or not.
    """
    # Initialize Google TTS and Google STT
    google_stt_obj = google_stt()
    google_tts_obj = google_tts()
    time_mins_old = round(time_seconds_old / 60, 1)
    time_mins_new = round(time_seconds_new / 60, 1)

    text = 'I\'m sorry, it looks like we cannot proceed with {} minutes for this exam, because the SNR criterion was ' \
           'not met. However, we can work with {} minutes. This could possibly change during the exam depending on ' \
           'the measured noise. Do you want to proceed? You can say \'Yes\' or \'No\'.'.format(time_mins_old,
                                                                                               time_mins_new)
    log('\n' + text)
    google_tts_obj.speak(text)
    while True:
        proceed = google_stt_obj.listen()
        if proceed.isalpha() and 'yes' in proceed.lower():
            return True
        elif proceed.isalpha() and 'no' in proceed.lower():
            return False
        else:
            text = 'Sorry, I couldn\'t understand that, let us try again. It looks like we cannot proceed with {} ' \
                   'minutes for this exam, because the SNR criterion was not met. However, we can work with {} ' \
                   'minutes. This could possibly change during the exam depending on the acquired noise. Do you want ' \
                   'to proceed? You can say \'Yes\' or \'No\'.'.format(time_mins_old, time_mins_new)
            google_tts_obj.speak(text)
