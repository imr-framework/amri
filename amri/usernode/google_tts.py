import os
from pathlib import Path

from google.cloud import texttospeech
from playsound import playsound


class google_tts:
    def __init__(self):
        script_path = os.path.abspath(__file__)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(
            Path(__file__).parent.parent / 'utils' / 'creds' / 'amri_stt_tts_key.json')
        self.voice = texttospeech.types.VoiceSelectionParams(language_code='en-US',
                                                             ssml_gender=texttospeech.enums.SsmlVoiceGender.FEMALE)
        self.audio_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.MP3,
                                                           speaking_rate=1.1)

    def speak(self, text):
        '''Synthesizes speech from the input string of text using Google Cloud.'''
        client = texttospeech.TextToSpeechClient()
        input_text = texttospeech.types.SynthesisInput(text=text)
        response = client.synthesize_speech(input_text, self.voice, self.audio_config)

        # The response's audio_content is binary.
        audio_file_path = Path(__file__).parent / 'output.mp3'
        with open(str(audio_file_path), 'wb') as out:
            out.write(response.audio_content)
        playsound(str(audio_file_path))
        audio_file_path.unlink()
