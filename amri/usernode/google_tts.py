import os

from google.cloud import texttospeech
from pygame import mixer


class google_tts:
    def __init__(self):
        script_path = os.path.abspath(__file__)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.path.dirname(script_path),
                                                                    'AMRI-TMC-7eb2c9543d48.json')
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
        audio_file_path = os.path.dirname(os.path.abspath(__file__))
        audio_file_path = os.path.normpath(os.path.join(audio_file_path, 'output.mp3'))
        with open(audio_file_path, 'wb') as out:
            out.write(response.audio_content)

        mixer.music.load(audio_file_path)
        mixer.music.play()
        while mixer.music.get_busy():
            pass
