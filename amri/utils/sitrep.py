import datetime
from pathlib import Path

from amri.utils import constants
from amri.utils.json_utils import JsonUtils
from amri.utils.log_utils import log
from amri.utils.pydrive_utils import PyDriveUtils


class Sitrep:

    def __init__(self):
        self.pydrive = PyDriveUtils()
        self.json_obj = JsonUtils()

        self.filename = 'sitrep.txt'
        self.MAC_SCAN_JOB_PATH = constants.MAC_SCAN_JOB_PATH
        self.sitrep_drive_file = self.pydrive.check_file_exists(self.filename, verbose=False)

        if self.sitrep_drive_file is not False:  # Older Sitrep exists
            # Wipe contents
            sitrep_json_str = self.sitrep_drive_file.GetContentString()
            sitrep_dict = self.json_obj.make_dict_from_json_str(sitrep_json_str)
            if 'patient_info' in sitrep_dict:
                self.sitrep_drive_file.Trash()
            else:
                self.sitrep_dict = sitrep_dict
                return

        self.sitrep_drive_file = self.pydrive.drive.CreateFile({'title': self.filename})
        self.sitrep_drive_file.Upload()
        now = datetime.datetime.now()
        now = now.strftime("%Y%b%d_%H:%M:%S")
        self.sitrep_dict = {'sitrep_file_id': [self.sitrep_drive_file['id'], now]}
        self.sitrep_dict['sitrep_created_by'] = {'unit_name': ['June'], 'unit_location': ['MBBI', now]}

        sitrep_json_str = self.json_obj.make_json_str_from_dict(self.sitrep_dict)
        self.json_obj.save_json_str_to_path(json_str=sitrep_json_str, path='temp.txt')
        self.sitrep_drive_file.SetContentFile('temp.txt')
        self.sitrep_drive_file.Upload()
        del self.sitrep_drive_file
        Path('temp.txt').unlink()

    def update_sitrep(self, verbose: bool = True):
        """Get latest Sitrep from Google Drive."""
        self.sitrep_drive_file = self.pydrive.check_file_exists(filename=self.filename, verbose=verbose)
        sitrep_json_str = self.pydrive.get_file_contents_as_string(drive_file=self.sitrep_drive_file, verbose=verbose)
        self.sitrep_dict = self.json_obj.make_dict_from_json_str(sitrep_json_str)

    def put_in_sitrep(self, key=None, value=None, nest_in=None, dict=None, verbose: bool = True):
        self.update_sitrep(verbose=verbose)
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
        self.json_obj.save_json_str_to_path(json_str=sitrep_json_str, path='temp.txt')
        self.sitrep_drive_file.SetContentFile('temp.txt')
        self.sitrep_drive_file.Upload()
        del self.sitrep_drive_file
        Path('temp.txt').unlink()

        if Path(self.MAC_SCAN_JOB_PATH).parent.exists():  # Check if directory exists
            self.json_obj.save_json_str_to_path(json_str=sitrep_json_str,
                                                path=self.MAC_SCAN_JOB_PATH)  # Also save to local

    def remove_from_sitrep(self, key: str, verbose: bool = True):
        self.update_sitrep(verbose=verbose)
        if key in self.sitrep_dict:
            self.sitrep_dict.pop(key)
            self.put_in_sitrep(key=None, value=None, dict=self.sitrep_dict, verbose=verbose)

    def get_from_sitrep(self, key, nested_in=None, ignore_issue: bool = False, verbose: bool = True):
        self.update_sitrep(verbose)
        temp_dict = self.sitrep_dict

        if not ignore_issue:
            if 'issue' in temp_dict:  # Check for any issues
                issue = temp_dict['issue'][0]
                return issue

        if nested_in is not None:
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
