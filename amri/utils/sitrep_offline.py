from amri.utils import constants
from amri.utils.json_utils import JsonUtils
from amri.utils.log_utils import log


class Sitrep_offline:
    def __init__(self):
        self.WIN_SCAN_JOB_PATH = constants.WIN_SCAN_JOB_PATH
        self.json_obj = JsonUtils()
        self.update_sitrep()

    def update_sitrep(self):
        """Get latest Sitrep from local"""
        sitrep_offline = open(self.WIN_SCAN_JOB_PATH, 'r')
        sitrep_json_str = sitrep_offline.read()
        self.sitrep_dict = self.json_obj.make_dict_from_json_str(sitrep_json_str)
        sitrep_offline.close()

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
