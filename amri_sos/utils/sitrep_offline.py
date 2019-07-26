import datetime
import os
import platform

from amri_sos.utils import constants
from amri_sos.utils.json_utils import JsonUtils
from amri_sos.utils.log_utils import log


class Sitrep_offline:
    def __init__(self):
        self.MAC_SCAN_JOB_PATH = constants.MAC_SCAN_JOB_PATH
        self.WIN_SCAN_JOB_PATH = constants.WIN_SCAN_JOB_PATH
        self.json_obj = JsonUtils()

        now = datetime.datetime.now()
        now = now.strftime("%Y%b%d_%H:%M:%S")
        self.sitrep_dict = {'sitrep_created_by': {'unit_name': ['June'], 'unit_location': ['MBBI', now]}}

        sitrep_json_str = self.json_obj.make_json_str_from_dict(self.sitrep_dict)
        if platform.system() == 'Darwin' and not self.MAC_SCAN_JOB_PATH.exists():
            self.json_obj.save_json_str_to_path(json_str=sitrep_json_str, path=self.MAC_SCAN_JOB_PATH)
        elif platform.system() == 'Windows' and not self.WIN_SCAN_JOB_PATH.exists():
            self.json_obj.save_json_str_to_path(json_str=sitrep_json_str, path=self.WIN_SCAN_JOB_PATH)

    def update_sitrep(self):
        """Get latest Sitrep from local"""
        if platform.system() == 'Darwin':
            sitrep_offline = open(self.MAC_SCAN_JOB_PATH, 'r')
        elif platform.system() == 'Windows':
            sitrep_offline = open(str(self.WIN_SCAN_JOB_PATH), 'r')
        sitrep_json_str = sitrep_offline.read()
        self.sitrep_dict = self.json_obj.make_dict_from_json_str(sitrep_json_str)
        sitrep_offline.close()

    def put_in_sitrep(self, key=None, value=None, nest_in=None, dict=None, verbose: bool = True):
        self.update_sitrep()
        now = datetime.datetime.now()
        now = now.strftime("%Y%b%d_%H:%M:%S")

        if key is None and value is None and dict is None:
            raise Exception('Code incomplete.')

        if dict is not None:
            self.sitrep_dict = dict
        else:
            if nest_in is None:
                self.sitrep_dict[key] = [value, now]
            elif nest_in is not None:
                nested_dict = self.sitrep_dict[nest_in] if nest_in in self.sitrep_dict else {}
                nested_dict[key] = [value, now]
                self.sitrep_dict[nest_in] = nested_dict

        # self.sitrep_dict['sitrep_last_update_millis'] = time.time()
        sitrep_json_str = self.json_obj.make_json_str_from_dict(self.sitrep_dict)

        if os.path.exists(os.path.dirname(self.MAC_SCAN_JOB_PATH)):  # Check if directory exists
            self.json_obj.save_json_str_to_path(json_str=sitrep_json_str,
                                                path=self.MAC_SCAN_JOB_PATH)  # Also save to local

    def get_from_sitrep(self, key, nested_in=None, verbose: bool = True):
        self.update_sitrep()

        if nested_in is None:
            temp_dict = self.sitrep_dict
        else:
            if nested_in in self.sitrep_dict:
                temp_dict = self.sitrep_dict[nested_in]
            else:
                log('{} not found in Sitrep, returning False'.format(key), verbose=verbose)
                return False
        if key in temp_dict:
            return temp_dict[key][0]
        else:
            log('{} not found in Sitrep, returning False'.format(key), verbose=verbose)
            return False
