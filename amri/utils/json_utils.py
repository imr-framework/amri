import json


class JsonUtils:
    def __init__(self):
        self.encoder = json.encoder.JSONEncoder()
        self.decoder = json.decoder.JSONDecoder()

    def make_json_str_from_dict(self, dict_to_encode: dict):
        return self.encoder.encode(dict_to_encode)

    def make_dict_from_json_str(self, json_str_to_decode: str):
        return self.decoder.decode(json_str_to_decode)

    def save_json_str_to_path(self, json_str, path):
        temp_file = open(path, 'w')
        json.dump(json.loads(json_str), temp_file, indent=4)
        temp_file.close()
